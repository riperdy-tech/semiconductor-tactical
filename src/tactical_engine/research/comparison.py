from pydantic import BaseModel, Field

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar
from tactical_engine.options.chain_provider import OptionChainProvider
from tactical_engine.reports.metrics import PerformanceMetrics, calculate_metrics
from tactical_engine.research.falsification import (
    BlockBootstrapResult,
    StrongestDayExclusionResult,
    TickerExclusionResult,
    run_strongest_day_exclusion_test,
    run_ticker_exclusion_test,
    stationary_block_bootstrap,
)
from tactical_engine.research.walk_forward import split_data_by_research_dates


class StrategyComparisonResult(BaseModel):
    literal_clone: PerformanceMetrics
    risk_controlled: PerformanceMetrics
    regime_adapted: PerformanceMetrics
    cost_sensitivity: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    leverage_sensitivity: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    ticker_exclusion: TickerExclusionResult | None = None
    strongest_day_exclusion: StrongestDayExclusionResult | None = None
    block_bootstrap: BlockBootstrapResult | None = None
    oos_comparison: dict[str, PerformanceMetrics] | None = None
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

    # 4. Cost sensitivity (0 bps, 5 bps, 10 bps, 15 bps slippage)
    cost_sens: dict[str, PerformanceMetrics] = {}
    for slip_bps in [0.0, 5.0, 10.0, 15.0]:
        c_dict = base_config.model_dump()
        c_dict["costs"]["equity_slippage_bps"] = slip_bps
        c_cfg = EngineConfig.model_validate(c_dict)
        c_res = run_backtest(data, c_cfg, option_chain_provider)
        cost_sens[f"{slip_bps:.0f}bps"] = calculate_metrics(c_res)

    # 5. Leverage sensitivity (1.0x, 1.25x, 1.5x, 2.0x, 3.0x)
    lev_sens: dict[str, PerformanceMetrics] = {}
    for lev in [1.0, 1.25, 1.5, 2.0, 3.0]:
        l_dict = base_config.model_dump()
        l_dict["portfolio"]["max_gross_leverage"] = lev
        l_dict["portfolio"]["max_symbol_weight"] = min(1.0, 0.25 * lev)
        l_cfg = EngineConfig.model_validate(l_dict)
        l_res = run_backtest(data, l_cfg, option_chain_provider)
        lev_sens[f"{lev:.2f}x"] = calculate_metrics(l_res)

    # 6. Falsification: Ticker Leave-One-Out
    ticker_ex = run_ticker_exclusion_test(data=data, config=risk_cfg)

    # 7. Falsification: Strongest-Day Exclusion Diagnostic
    day_ex = run_strongest_day_exclusion_test(
        trades=risk_res.trades, initial_cash=risk_cfg.portfolio.initial_cash
    )

    # 8. Falsification: Stationary Block Bootstrap on Benchmark / Universe Returns
    benchmark_bars = data.get("SMH") or (next(iter(data.values())) if data else [])
    block_boot = stationary_block_bootstrap(
        bars=benchmark_bars, expected_block_size=20, num_simulations=500
    )

    # 9. Out-of-sample segmentation if dates configured
    oos_comp = None
    splits = split_data_by_research_dates(data, base_config.research)
    if splits and any(splits["in_sample"].values()) and any(splits["out_of_sample"].values()):
        res_is = run_backtest(splits["in_sample"], base_config, option_chain_provider)
        res_oos = run_backtest(splits["out_of_sample"], base_config, option_chain_provider)
        oos_comp = {
            "in_sample": calculate_metrics(res_is),
            "out_of_sample": calculate_metrics(res_oos),
        }

    return StrategyComparisonResult(
        literal_clone=clone_metrics,
        risk_controlled=risk_metrics,
        regime_adapted=regime_metrics,
        cost_sensitivity=cost_sens,
        leverage_sensitivity=lev_sens,
        ticker_exclusion=ticker_ex,
        strongest_day_exclusion=day_ex,
        block_bootstrap=block_boot,
        oos_comparison=oos_comp,
    )

