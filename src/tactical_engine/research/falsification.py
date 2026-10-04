from collections import defaultdict
from datetime import timedelta

import numpy as np
from pydantic import BaseModel, Field

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.backtest.state import TradeRecord
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar
from tactical_engine.reports.metrics import PerformanceMetrics, calculate_metrics


class BlockBootstrapResult(BaseModel):
    diagnostic_name: str = "Benchmark Return Dependence Diagnostic"
    resampling_unit: str = "benchmark_bar_returns"
    period_scope: str = "FULL"
    symbol: str = "SMH"
    mean_return_pct: float
    median_return_pct: float
    ci_lower_pct: float
    ci_upper_pct: float
    prob_positive: float
    simulated_returns: list[float] = Field(default_factory=list)


class StrategyRobustnessResult(BaseModel):
    diagnostic_name: str = "Strategy-Level Return Robustness Diagnostic"
    resampling_unit: str = "strategy_daily_returns"
    period_scope: str = "FULL"
    observation_definition: str = (
        "Complete daily trading session return (% of initial equity); "
        "inactive sessions receive 0.0% return"
    )
    mean_return_pct: float = 0.0
    median_return_pct: float = 0.0
    ci_lower_pct: float = 0.0
    ci_upper_pct: float = 0.0
    prob_positive: float = 0.0
    sample_size: int = 0
    active_trading_days: int = 0
    inactive_sessions: int = 0
    is_sufficient_sample: bool = True
    insufficient_reason: str | None = None
    simulated_returns: list[float] = Field(default_factory=list)


def strategy_return_bootstrap(
    trades: list[TradeRecord],
    initial_cash: float = 100_000.0,
    expected_block_size: int = 5,
    num_simulations: int = 500,
    confidence_level: float = 0.95,
    seed: int = 42,
    evaluation_dates: list[str] | None = None,
    period_scope: str = "FULL",
) -> StrategyRobustnessResult:
    """Politis & Romano (1994) stationary block bootstrap on complete daily strategy returns.

    Resamples blocks of consecutive daily session returns over the evaluation period
    (including zero-return inactive sessions) to preserve autocorrelation and
    volatility clustering in realized strategy outcomes.
    """
    # 1. Map realized trade net P&L by exit calendar date (YYYY-MM-DD)
    day_pnls: dict[str, float] = defaultdict(float)
    active_days_set: set[str] = set()
    for t in trades:
        day_str = t.exit_time.strftime("%Y-%m-%d")
        day_pnls[day_str] += t.net_pnl
        active_days_set.add(day_str)

    # 2. Build complete session/day axis
    if evaluation_dates:
        # Retain explicit session dates, union with any trade exit dates
        all_sessions = sorted(list(set(evaluation_dates).union(day_pnls.keys())))
    elif trades:
        # Reconstruct weekday sessions between earliest entry and latest exit
        min_date = min(t.entry_time.date() for t in trades)
        max_date = max(t.exit_time.date() for t in trades)
        sessions: list[str] = []
        cur = min_date
        while cur <= max_date:
            if cur.weekday() < 5:  # Mon-Fri
                sessions.append(cur.strftime("%Y-%m-%d"))
            cur += timedelta(days=1)
        all_sessions = sorted(list(set(sessions).union(day_pnls.keys())))
    else:
        all_sessions = []

    n_sessions = len(all_sessions)
    n_active = len(active_days_set)
    n_inactive = n_sessions - n_active

    # 3. Sample sufficiency check
    if not trades or n_active == 0:
        return StrategyRobustnessResult(
            period_scope=period_scope,
            sample_size=n_sessions,
            active_trading_days=0,
            inactive_sessions=n_sessions,
            is_sufficient_sample=False,
            insufficient_reason="INSUFFICIENT_SAMPLE: zero trades executed in evaluation period",
        )

    if n_sessions < 10:
        return StrategyRobustnessResult(
            period_scope=period_scope,
            sample_size=n_sessions,
            active_trading_days=n_active,
            inactive_sessions=n_inactive,
            is_sufficient_sample=False,
            insufficient_reason=(
                f"INSUFFICIENT_SAMPLE: only {n_sessions} complete sessions (minimum 10 required)"
            ),
        )

    if n_active < 10:
        return StrategyRobustnessResult(
            period_scope=period_scope,
            sample_size=n_sessions,
            active_trading_days=n_active,
            inactive_sessions=n_inactive,
            is_sufficient_sample=False,
            insufficient_reason=(
                f"INSUFFICIENT_SAMPLE: only {n_active} active trading days (minimum 10 required)"
            ),
        )

    # 4. Construct complete daily return array (inactive sessions receive 0.0)
    daily_returns = np.array(
        [day_pnls.get(s, 0.0) / initial_cash for s in all_sessions], dtype=float
    )
    n = len(daily_returns)

    p = 1.0 / max(1, expected_block_size)
    rng = np.random.default_rng(seed)

    sim_cumulative_returns = []
    for _ in range(num_simulations):
        resampled_returns = np.empty(n, dtype=float)
        idx = rng.integers(0, n)
        for t_idx in range(n):
            if rng.random() < p:
                idx = rng.integers(0, n)
            else:
                idx = (idx + 1) % n
            resampled_returns[t_idx] = daily_returns[idx]

        total_ret = float(np.sum(resampled_returns)) * 100.0
        sim_cumulative_returns.append(round(total_ret, 2))

    sorted_rets = np.sort(sim_cumulative_returns)
    alpha = 1.0 - confidence_level
    lower_idx = int(num_simulations * (alpha / 2.0))
    upper_idx = int(num_simulations * (1.0 - alpha / 2.0))

    mean_ret = float(np.mean(sorted_rets))
    median_ret = float(np.median(sorted_rets))
    ci_lower = float(sorted_rets[lower_idx])
    ci_upper = float(sorted_rets[min(upper_idx, num_simulations - 1)])
    prob_pos = float(np.mean(sorted_rets > 0))

    return StrategyRobustnessResult(
        period_scope=period_scope,
        mean_return_pct=round(mean_ret, 2),
        median_return_pct=round(median_ret, 2),
        ci_lower_pct=round(ci_lower, 2),
        ci_upper_pct=round(ci_upper, 2),
        prob_positive=round(prob_pos, 4),
        sample_size=n,
        active_trading_days=n_active,
        inactive_sessions=n_inactive,
        is_sufficient_sample=True,
        simulated_returns=sim_cumulative_returns[:50],
    )


def stationary_block_bootstrap(
    bars: list[Bar],
    expected_block_size: int = 20,
    num_simulations: int = 500,
    confidence_level: float = 0.95,
    seed: int = 42,
    symbol: str = "SMH",
    period_scope: str = "FULL",
) -> BlockBootstrapResult:
    """Politis & Romano (1994) stationary block bootstrap for autocorrelated return series.

    Blocks have geometrically distributed lengths with mean expected_block_size.
    """
    if len(bars) < expected_block_size + 2:
        return BlockBootstrapResult(
            period_scope=period_scope,
            symbol=symbol,
            mean_return_pct=0.0,
            median_return_pct=0.0,
            ci_lower_pct=0.0,
            ci_upper_pct=0.0,
            prob_positive=0.0,
        )

    closes = np.array([b.close for b in bars], dtype=float)
    log_returns = np.diff(np.log(closes))
    n = len(log_returns)

    p = 1.0 / max(1, expected_block_size)
    rng = np.random.default_rng(seed)

    sim_cumulative_returns = []

    for _ in range(num_simulations):
        resampled_returns = np.empty(n, dtype=float)
        idx = rng.integers(0, n)
        for t in range(n):
            if rng.random() < p:
                idx = rng.integers(0, n)
            else:
                idx = (idx + 1) % n
            resampled_returns[t] = log_returns[idx]

        total_ret = float(np.exp(np.sum(resampled_returns)) - 1.0) * 100.0
        sim_cumulative_returns.append(round(total_ret, 2))

    sorted_rets = np.sort(sim_cumulative_returns)
    alpha = 1.0 - confidence_level
    lower_idx = int(num_simulations * (alpha / 2.0))
    upper_idx = int(num_simulations * (1.0 - alpha / 2.0))

    mean_ret = float(np.mean(sorted_rets))
    median_ret = float(np.median(sorted_rets))
    ci_lower = float(sorted_rets[lower_idx])
    ci_upper = float(sorted_rets[min(upper_idx, num_simulations - 1)])
    prob_pos = float(np.mean(sorted_rets > 0))

    return BlockBootstrapResult(
        period_scope=period_scope,
        symbol=symbol,
        mean_return_pct=round(mean_ret, 2),
        median_return_pct=round(median_ret, 2),
        ci_lower_pct=round(ci_lower, 2),
        ci_upper_pct=round(ci_upper, 2),
        prob_positive=round(prob_pos, 4),
        simulated_returns=sim_cumulative_returns[:50],
    )


class TickerExclusionResult(BaseModel):
    period_scope: str = "FULL"
    scope_note: str = (
        "Full-sample diagnostic only (evaluates ticker concentration across entire dataset)"
    )
    baseline_metrics: PerformanceMetrics
    results_by_excluded_ticker: dict[str, PerformanceMetrics] = Field(default_factory=dict)
    dominant_ticker: str | None = None
    is_fragile_to_single_ticker: bool = False


def run_ticker_exclusion_test(
    data: dict[str, list[Bar]],
    config: EngineConfig,
) -> TickerExclusionResult:
    """Leave-one-out ticker exclusion test to verify return is not driven by an outlier ticker."""
    baseline_result = run_backtest(data=data, config=config)
    baseline_metrics = calculate_metrics(baseline_result)

    results: dict[str, PerformanceMetrics] = {}
    base_pnl = baseline_metrics.net_pnl

    max_pnl_drop = 0.0
    dominant_sym = None

    for sym in data.keys():
        sub_data = {s: bars for s, bars in data.items() if s != sym}
        if not sub_data:
            continue

        cfg_copy = config.model_dump()
        cfg_copy["strategy"]["universe"] = [s for s in config.strategy.universe if s != sym]
        if config.strategy.two_x_etfs:
            cfg_copy["strategy"]["two_x_etfs"] = [s for s in config.strategy.two_x_etfs if s != sym]
        sub_cfg = EngineConfig.model_validate(cfg_copy)

        res = run_backtest(data=sub_data, config=sub_cfg)
        metrics = calculate_metrics(res)
        results[sym] = metrics

        pnl_drop = base_pnl - metrics.net_pnl
        if pnl_drop > max_pnl_drop:
            max_pnl_drop = pnl_drop
            dominant_sym = sym

    # If dropping a single ticker wipes out > 80% of net P&L (when baseline was positive)
    is_fragile = False
    if base_pnl > 0 and dominant_sym is not None:
        pnl_share = max_pnl_drop / base_pnl
        if pnl_share >= 0.80:
            is_fragile = True

    return TickerExclusionResult(
        period_scope="FULL",
        baseline_metrics=baseline_metrics,
        results_by_excluded_ticker=results,
        dominant_ticker=dominant_sym,
        is_fragile_to_single_ticker=is_fragile,
    )


class StrongestDayExclusionResult(BaseModel):
    period_scope: str = "FULL"
    scope_note: str = (
        "Full-sample diagnostic only (evaluates single-day outlier "
        "dependency across entire dataset)"
    )
    baseline_net_pnl: float
    total_trading_days: int
    top_day_dates: list[str]
    top_day_pnls: list[float]
    pnl_excluding_top_1: float
    pnl_excluding_top_3: float
    pnl_excluding_top_5: float
    remains_positive_top_1: bool
    remains_positive_top_3: bool
    remains_positive_top_5: bool


def run_strongest_day_exclusion_test(
    trades: list[TradeRecord],
    initial_cash: float = 100_000.0,
) -> StrongestDayExclusionResult:
    """Excludes top 1, 3, and 5 strongest P&L days to test return dependency on single outliers."""
    if not trades:
        return StrongestDayExclusionResult(
            period_scope="FULL",
            baseline_net_pnl=0.0,
            total_trading_days=0,
            top_day_dates=[],
            top_day_pnls=[],
            pnl_excluding_top_1=0.0,
            pnl_excluding_top_3=0.0,
            pnl_excluding_top_5=0.0,
            remains_positive_top_1=False,
            remains_positive_top_3=False,
            remains_positive_top_5=False,
        )

    # Group net P&L by exit calendar date
    day_pnls: dict[str, float] = defaultdict(float)
    for t in trades:
        day_str = t.exit_time.strftime("%Y-%m-%d")
        day_pnls[day_str] += t.net_pnl

    total_pnl = sum(t.net_pnl for t in trades)
    sorted_days = sorted(day_pnls.items(), key=lambda x: x[1], reverse=True)

    top_dates = [d for d, _ in sorted_days[:5]]
    top_pnls = [round(p, 2) for _, p in sorted_days[:5]]

    top1_sum = sum(p for _, p in sorted_days[:1])
    top3_sum = sum(p for _, p in sorted_days[:3])
    top5_sum = sum(p for _, p in sorted_days[:5])

    pnl_ex_1 = round(total_pnl - top1_sum, 2)
    pnl_ex_3 = round(total_pnl - top3_sum, 2)
    pnl_ex_5 = round(total_pnl - top5_sum, 2)

    return StrongestDayExclusionResult(
        baseline_net_pnl=round(total_pnl, 2),
        total_trading_days=len(day_pnls),
        top_day_dates=top_dates,
        top_day_pnls=top_pnls,
        pnl_excluding_top_1=pnl_ex_1,
        pnl_excluding_top_3=pnl_ex_3,
        pnl_excluding_top_5=pnl_ex_5,
        remains_positive_top_1=pnl_ex_1 > 0,
        remains_positive_top_3=pnl_ex_3 > 0,
        remains_positive_top_5=pnl_ex_5 > 0,
    )
