from pydantic import BaseModel, Field

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar
from tactical_engine.options.chain_provider import OptionChainProvider
from tactical_engine.reports.metrics import PerformanceMetrics, calculate_metrics


class StrategyComparisonResult(BaseModel):
    literal_clone: PerformanceMetrics
    risk_controlled: PerformanceMetrics
    regime_adapted: PerformanceMetrics
    cost_sensitivity: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    leverage_sensitivity: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    options_contribution: PerformanceMetrics | None = None


def run_strategy_comparison(
    data: dict[str, list[Bar]],
    base_config: EngineConfig,
    option_chain_provider: OptionChainProvider | None = None,
) -> StrategyComparisonResult:
    # 1. Variant A — literal_clone (higher leverage, 2 layers, no sector filter)
    clone_cfg_dict = base_config.model_dump()
    clone_cfg_dict["strategy"]["variant"] = "literal_clone"
    clone_cfg_dict["portfolio"]["max_gross_leverage"] = 1.5
    clone_cfg_dict["portfolio"]["max_symbol_weight"] = 0.50
    clone_cfg_dict["portfolio"]["max_layers"] = 2
    clone_cfg_dict["signals"]["sector_filter"] = False
    clone_cfg = EngineConfig.model_validate(clone_cfg_dict)
    clone_res = run_backtest(data, clone_cfg, option_chain_provider)
    clone_metrics = calculate_metrics(clone_res)

    # 2. Variant B — risk_controlled (1.0x leverage, fixed risk sizing, strict stop)
    risk_cfg_dict = base_config.model_dump()
    risk_cfg_dict["strategy"]["variant"] = "risk_controlled"
    risk_cfg_dict["portfolio"]["max_gross_leverage"] = 1.0
    risk_cfg_dict["portfolio"]["max_symbol_weight"] = 0.25
    risk_cfg_dict["portfolio"]["max_layers"] = 1
    risk_cfg_dict["signals"]["sector_filter"] = False
    risk_cfg = EngineConfig.model_validate(risk_cfg_dict)
    risk_res = run_backtest(data, risk_cfg, option_chain_provider)
    risk_metrics = calculate_metrics(risk_res)

    # 3. Variant C — regime_adapted (risk_controlled + sector trend filter)
    regime_cfg_dict = base_config.model_dump()
    regime_cfg_dict["strategy"]["variant"] = "regime_adapted"
    regime_cfg_dict["portfolio"]["max_gross_leverage"] = 1.0
    regime_cfg_dict["portfolio"]["max_symbol_weight"] = 0.25
    regime_cfg_dict["portfolio"]["max_layers"] = 1
    regime_cfg_dict["signals"]["sector_filter"] = True
    regime_cfg = EngineConfig.model_validate(regime_cfg_dict)
    regime_res = run_backtest(data, regime_cfg, option_chain_provider)
    regime_metrics = calculate_metrics(regime_res)

    # 4. Cost sensitivity (0 bps, 5 bps, 15 bps slippage)
    cost_sens: dict[str, PerformanceMetrics] = {}
    for slip_bps in [0.0, 5.0, 15.0]:
        c_dict = base_config.model_dump()
        c_dict["costs"]["equity_slippage_bps"] = slip_bps
        c_cfg = EngineConfig.model_validate(c_dict)
        c_res = run_backtest(data, c_cfg, option_chain_provider)
        cost_sens[f"{slip_bps:.0f}bps"] = calculate_metrics(c_res)

    # 5. Leverage sensitivity (1.0x, 1.5x, 2.0x)
    lev_sens: dict[str, PerformanceMetrics] = {}
    for lev in [1.0, 1.5, 2.0]:
        l_dict = base_config.model_dump()
        l_dict["portfolio"]["max_gross_leverage"] = lev
        l_dict["portfolio"]["max_symbol_weight"] = min(1.0, 0.25 * lev)
        l_cfg = EngineConfig.model_validate(l_dict)
        l_res = run_backtest(data, l_cfg, option_chain_provider)
        lev_sens[f"{lev:.1f}x"] = calculate_metrics(l_res)

    return StrategyComparisonResult(
        literal_clone=clone_metrics,
        risk_controlled=risk_metrics,
        regime_adapted=regime_metrics,
        cost_sensitivity=cost_sens,
        leverage_sensitivity=lev_sens,
    )
