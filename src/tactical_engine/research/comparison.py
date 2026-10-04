from pydantic import BaseModel, Field

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar
from tactical_engine.options.chain_provider import OptionChainProvider
from tactical_engine.reports.metrics import PerformanceMetrics, calculate_metrics
from tactical_engine.research.falsification import (
    BlockBootstrapResult,
    StrategyRobustnessResult,
    StrongestDayExclusionResult,
    TickerExclusionResult,
    run_strongest_day_exclusion_test,
    run_ticker_exclusion_test,
    stationary_block_bootstrap,
    strategy_return_bootstrap,
)
from tactical_engine.research.walk_forward import split_data_train_val_test


class StrategyComparisonResult(BaseModel):
    literal_clone: PerformanceMetrics
    risk_controlled: PerformanceMetrics
    regime_adapted: PerformanceMetrics
    cost_sensitivity: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    leverage_sensitivity: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    ticker_exclusion: TickerExclusionResult | None = None
    strongest_day_exclusion: StrongestDayExclusionResult | None = None
    benchmark_bootstrap: BlockBootstrapResult | None = None
    strategy_bootstrap: StrategyRobustnessResult | None = None
    oos_available: bool = False
    oos_status_reason: str | None = None
    train_metrics: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    validation_metrics: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    test_metrics: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    oos_strategy_bootstrap: StrategyRobustnessResult | None = None
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

    # 6. Falsification: Ticker Leave-One-Out (evaluated on risk_controlled baseline)
    ticker_ex = run_ticker_exclusion_test(data=data, config=risk_cfg)

    # 7. Falsification: Strongest-Day Exclusion Diagnostic
    day_ex = run_strongest_day_exclusion_test(
        trades=risk_res.trades, initial_cash=risk_cfg.portfolio.initial_cash
    )

    # 8. Falsification: Benchmark Return Dependence Diagnostic (Market Returns)
    benchmark_bars = data.get("SMH") or (next(iter(data.values())) if data else [])
    benchmark_boot = stationary_block_bootstrap(
        bars=benchmark_bars,
        expected_block_size=20,
        num_simulations=500,
        symbol="SMH",
        period_scope="FULL",
    )

    # 9. Falsification: Strategy-Level Return Robustness Diagnostic (Daily Strategy Returns)
    full_sessions = sorted(
        {b.timestamp.strftime("%Y-%m-%d") for bars in data.values() for b in bars}
    )
    strategy_boot = strategy_return_bootstrap(
        trades=risk_res.trades,
        initial_cash=risk_cfg.portfolio.initial_cash,
        num_simulations=500,
        evaluation_dates=full_sessions,
        period_scope="FULL",
    )

    # 10. Out-of-Sample Train / Validation / Test Segmentation
    oos_splits = split_data_train_val_test(data, base_config.research)
    oos_avail = oos_splits.is_available
    oos_reason = oos_splits.status_reason

    train_m: dict[str, PerformanceMetrics] = {}
    val_m: dict[str, PerformanceMetrics] = {}
    test_m: dict[str, PerformanceMetrics] = {}
    oos_strat_boot: StrategyRobustnessResult | None = None
    legacy_oos_comp: dict[str, PerformanceMetrics] | None = None

    if oos_avail:
        # Run all 3 variants across disjoint partitions
        res_tr_c = run_backtest(oos_splits.train, clone_cfg, option_chain_provider)
        res_va_c = run_backtest(oos_splits.validation, clone_cfg, option_chain_provider)
        res_te_c = run_backtest(oos_splits.test, clone_cfg, option_chain_provider)
        train_m["literal_clone"] = calculate_metrics(res_tr_c)
        val_m["literal_clone"] = calculate_metrics(res_va_c)
        test_m["literal_clone"] = calculate_metrics(res_te_c)

        res_tr_r = run_backtest(oos_splits.train, risk_cfg, option_chain_provider)
        res_va_r = run_backtest(oos_splits.validation, risk_cfg, option_chain_provider)
        res_te_r = run_backtest(oos_splits.test, risk_cfg, option_chain_provider)
        train_m["risk_controlled"] = calculate_metrics(res_tr_r)
        val_m["risk_controlled"] = calculate_metrics(res_va_r)
        test_m["risk_controlled"] = calculate_metrics(res_te_r)

        res_tr_g = run_backtest(oos_splits.train, regime_cfg, option_chain_provider)
        res_va_g = run_backtest(oos_splits.validation, regime_cfg, option_chain_provider)
        res_te_g = run_backtest(oos_splits.test, regime_cfg, option_chain_provider)
        train_m["regime_adapted"] = calculate_metrics(res_tr_g)
        val_m["regime_adapted"] = calculate_metrics(res_va_g)
        test_m["regime_adapted"] = calculate_metrics(res_te_g)

        # Final untouched test/OOS robustness evaluation
        test_sessions = sorted(
            {b.timestamp.strftime("%Y-%m-%d") for bars in oos_splits.test.values() for b in bars}
        )
        oos_strat_boot = strategy_return_bootstrap(
            trades=res_te_r.trades,
            initial_cash=risk_cfg.portfolio.initial_cash,
            num_simulations=500,
            evaluation_dates=test_sessions,
            period_scope="TEST_OOS",
        )

        legacy_oos_comp = {
            "train": train_m["risk_controlled"],
            "validation": val_m["risk_controlled"],
            "test": test_m["risk_controlled"],
        }

    return StrategyComparisonResult(
        literal_clone=clone_metrics,
        risk_controlled=risk_metrics,
        regime_adapted=regime_metrics,
        cost_sensitivity=cost_sens,
        leverage_sensitivity=lev_sens,
        ticker_exclusion=ticker_ex,
        strongest_day_exclusion=day_ex,
        benchmark_bootstrap=benchmark_boot,
        strategy_bootstrap=strategy_boot,
        oos_available=oos_avail,
        oos_status_reason=oos_reason,
        train_metrics=train_m,
        validation_metrics=val_m,
        test_metrics=test_m,
        oos_strategy_bootstrap=oos_strat_boot,
        oos_comparison=legacy_oos_comp,
    )
