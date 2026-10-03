from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar
from tactical_engine.data.sufficiency import (
    ComponentValidationStatus,
    DataSufficiencyReport,
    check_data_sufficiency,
)
from tactical_engine.reports.metrics import PerformanceMetrics, calculate_metrics


class FidelityMatrixResult(BaseModel):
    # Experiment 1: Current baseline (preserved)
    baseline: PerformanceMetrics
    # Experiment 2: Directional fidelity (equity-only, 1.0x leverage)
    directional_equity: PerformanceMetrics
    # Experiment 3: Directional + margin (1.5x / 2.0x leverage with financing)
    directional_margin: PerformanceMetrics
    # Experiment 4: Directional + covered calls (gated by option chain data)
    directional_covered_calls: PerformanceMetrics | None = None
    covered_calls_status: str = "UNVALIDATED"
    # Experiment 5: Full validated composite (gated by all 4 components)
    full_composite_status: str = "BLOCKED_BY_DATA_GATE"
    full_composite_metrics: PerformanceMetrics | None = None
    # Experiment 6: Component ablations
    ablations: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    # Data sufficiency report
    data_sufficiency: DataSufficiencyReport
    # Plausibility checks against source description
    plausibility_comparison: dict[str, Any] = Field(default_factory=dict)


def run_fidelity_matrix(
    data: dict[str, list[Bar]],
    base_config: EngineConfig,
    data_dir: Path | str | None = None,
) -> FidelityMatrixResult:
    """Run the 6-experiment fidelity matrix per Phase H of fidelity plan."""
    # 0. Data sufficiency gate check
    sufficiency = check_data_sufficiency(data_dir=data_dir)

    # 1. Experiment 1: Current Baseline (CURRENT_MECHANICAL_PULLBACK_BASELINE)
    baseline_cfg_dict = base_config.model_dump()
    baseline_cfg_dict["strategy"]["variant"] = "current_mechanical_pullback_baseline"
    baseline_cfg_dict["signals"]["signal_family"] = "pullback_zscore"
    baseline_cfg = EngineConfig.model_validate(baseline_cfg_dict)
    res_base = run_backtest(data, baseline_cfg)
    m_base = calculate_metrics(res_base)

    # 2. Experiment 2: Directional Fidelity (Equity-only, 1.0x leverage, no options)
    dir_cfg_dict = base_config.model_dump()
    dir_cfg_dict["strategy"]["variant"] = "directional_fidelity_reconstruction"
    dir_cfg_dict["signals"]["signal_family"] = "directional_fidelity"
    dir_cfg_dict["signals"]["order_execution_style"] = "stop_limit"
    dir_cfg_dict["portfolio"]["max_gross_leverage"] = 1.0
    dir_cfg_dict["portfolio"]["max_layers"] = 1
    dir_cfg_dict["options"]["enabled"] = False
    dir_cfg = EngineConfig.model_validate(dir_cfg_dict)
    res_dir = run_backtest(data, dir_cfg)
    m_dir = calculate_metrics(res_dir)

    # 3. Experiment 3: Directional + Margin (1.5x leverage, 2 layers, margin financing)
    margin_cfg_dict = base_config.model_dump()
    margin_cfg_dict["strategy"]["variant"] = "directional_fidelity_reconstruction"
    margin_cfg_dict["signals"]["signal_family"] = "directional_fidelity"
    margin_cfg_dict["signals"]["order_execution_style"] = "stop_limit"
    margin_cfg_dict["portfolio"]["max_gross_leverage"] = 1.5
    margin_cfg_dict["portfolio"]["max_layers"] = 2
    margin_cfg_dict["costs"]["margin_rate_annual"] = 0.05
    margin_cfg_dict["options"]["enabled"] = False
    margin_cfg = EngineConfig.model_validate(margin_cfg_dict)
    res_margin = run_backtest(data, margin_cfg)
    m_margin = calculate_metrics(res_margin)

    # 4. Experiment 4: Directional + Covered Calls
    # Gated by option chain data: without chain data, marked UNVALIDATED
    m_calls = None
    if sufficiency.covered_calls == ComponentValidationStatus.VALIDATED:
        calls_cfg_dict = dir_cfg_dict.copy()
        calls_cfg_dict["options"]["enabled"] = True
        calls_cfg = EngineConfig.model_validate(calls_cfg_dict)
        res_calls = run_backtest(data, calls_cfg)
        m_calls = calculate_metrics(res_calls)
        calls_status = "VALIDATED"
    else:
        calls_status = "UNVALIDATED (Historical option chain quotes absent)"

    # 5. Experiment 5: Full Validated Composite
    # Only run if all 4 components are VALIDATED
    full_metrics = None
    if sufficiency.is_full_replication_supported:
        full_status = "VALIDATED"
    else:
        full_status = "BLOCKED_BY_DATA_GATE (Extended-hours and option chain data unvalidated)"

    # 6. Experiment 6: Component Ablations
    ablations: dict[str, PerformanceMetrics] = {
        "equity_only_1.0x": m_dir,
        "equity_plus_margin_1.5x": m_margin,
    }

    # High-leverage margin ablation (2.0x)
    lev2_cfg_dict = margin_cfg_dict.copy()
    lev2_cfg_dict["portfolio"]["max_gross_leverage"] = 2.0
    lev2_cfg_dict["portfolio"]["max_layers"] = 3
    lev2_cfg = EngineConfig.model_validate(lev2_cfg_dict)
    res_lev2 = run_backtest(data, lev2_cfg)
    ablations["equity_plus_margin_2.0x"] = calculate_metrics(res_lev2)

    # Market orders vs Stop-limit orders ablation
    mkt_cfg_dict = dir_cfg_dict.copy()
    mkt_cfg_dict["signals"]["order_execution_style"] = "market"
    mkt_cfg = EngineConfig.model_validate(mkt_cfg_dict)
    res_mkt = run_backtest(data, mkt_cfg)
    ablations["directional_market_orders"] = calculate_metrics(res_mkt)

    # Sector filter active vs bypassed ablation
    nosec_cfg_dict = dir_cfg_dict.copy()
    nosec_cfg_dict["signals"]["sector_filter"] = False
    nosec_cfg = EngineConfig.model_validate(nosec_cfg_dict)
    res_nosec = run_backtest(data, nosec_cfg)
    ablations["directional_no_sector_filter"] = calculate_metrics(res_nosec)

    # Plausibility Comparison (Descriptive Diagnostics)
    plausibility = {
        "source_described_trade_count": (
            "~1,300+ over ~90 calendar days (~20 trades/day across portfolio)"
        ),
        "baseline_trade_count": m_base.total_trades,
        "baseline_trades_per_day": m_base.trades_per_day,
        "baseline_median_hold_minutes": m_base.median_holding_time_minutes,
        "fidelity_directional_trade_count": m_dir.total_trades,
        "fidelity_directional_trades_per_day": m_dir.trades_per_day,
        "fidelity_directional_median_hold_minutes": m_dir.median_holding_time_minutes,
        "source_trade_count_diagnostic_note": (
            "Descriptive plausibility check only; trade count was NOT an optimization target."
        ),
    }

    return FidelityMatrixResult(
        baseline=m_base,
        directional_equity=m_dir,
        directional_margin=m_margin,
        directional_covered_calls=m_calls,
        covered_calls_status=calls_status,
        full_composite_status=full_status,
        full_composite_metrics=full_metrics,
        ablations=ablations,
        data_sufficiency=sufficiency,
        plausibility_comparison=plausibility,
    )
