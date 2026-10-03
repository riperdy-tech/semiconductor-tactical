import numpy as np
from pydantic import BaseModel

from tactical_engine.backtest.engine import BacktestResult


class PerformanceMetrics(BaseModel):
    initial_cash: float
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    total_trades: int
    win_rate: float
    profit_factor: float
    expectancy_per_trade: float
    gross_pnl: float
    net_pnl: float
    cost_drag_pct: float
    margin_interest_paid: float = 0.0
    peak_margin_debt: float = 0.0
    margin_call_count: int = 0
    forced_liquidation_count: int = 0
    options_premium_collected: float = 0.0
    options_realized_pnl: float = 0.0
    options_validation_status: str = "NONE"
    implementation_label: str = "CURRENT_MECHANICAL_PULLBACK_BASELINE"
    # Trade-frequency diagnostics
    total_signals_generated: int = 0
    filled_entries_count: int = 0
    max_simultaneous_positions: int = 0
    reentry_count: int = 0
    time_in_market_pct: float = 0.0
    trades_per_day: float = 0.0
    trades_per_symbol_per_day: float = 0.0
    median_holding_time_minutes: float = 0.0
    # Cost decomposition
    commission_paid: float = 0.0
    slippage_paid: float = 0.0
    total_cost_paid: float = 0.0
    costs_as_pct_of_gross_pnl: float = 0.0


def calculate_metrics(result: BacktestResult) -> PerformanceMetrics:
    init_c = result.initial_cash
    final_eq = result.final_equity
    tot_ret = ((final_eq - init_c) / init_c) * 100.0 if init_c > 0 else 0.0

    # Max Drawdown
    eq = np.array(result.equity_curve)
    if len(eq) > 0:
        peaks = np.maximum.accumulate(eq)
        drawdowns = (peaks - eq) / peaks
        max_dd = float(np.max(drawdowns)) * 100.0
    else:
        max_dd = 0.0

    # Trade stats
    trades = result.trades
    total_trades = len(trades)
    if total_trades > 0:
        wins = [t for t in trades if t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl <= 0]
        win_rate = len(wins) / total_trades
        gross_profit = sum(t.net_pnl for t in wins)
        gross_loss = abs(sum(t.net_pnl for t in losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")
        net_pnl = sum(t.net_pnl for t in trades)
        gross_pnl = sum(t.gross_pnl for t in trades)
        expectancy = net_pnl / total_trades
        cost_drag = ((gross_pnl - net_pnl) / abs(gross_pnl)) * 100.0 if gross_pnl != 0 else 0.0
    else:
        win_rate = 0.0
        profit_factor = 0.0
        net_pnl = 0.0
        gross_pnl = 0.0
        expectancy = 0.0
        cost_drag = 0.0

    return PerformanceMetrics(
        initial_cash=init_c,
        final_equity=final_eq,
        total_return_pct=round(tot_ret, 2),
        max_drawdown_pct=round(max_dd, 2),
        total_trades=total_trades,
        win_rate=round(win_rate, 4),
        profit_factor=round(profit_factor, 2),
        expectancy_per_trade=round(expectancy, 2),
        gross_pnl=round(gross_pnl, 2),
        net_pnl=round(net_pnl, 2),
        cost_drag_pct=round(cost_drag, 2),
        margin_interest_paid=round(result.margin_interest_paid, 2),
        peak_margin_debt=round(result.peak_margin_debt, 2),
        margin_call_count=result.margin_call_count,
        forced_liquidation_count=result.forced_liquidation_count,
        options_premium_collected=round(result.options_premium_collected, 2),
        options_realized_pnl=round(result.options_realized_pnl, 2),
        implementation_label=getattr(
            result, "implementation_label", "CURRENT_MECHANICAL_PULLBACK_BASELINE"
        ),
        total_signals_generated=result.total_signals_generated,
        filled_entries_count=result.filled_entries_count,
        max_simultaneous_positions=result.max_simultaneous_positions,
        reentry_count=result.reentry_count,
        time_in_market_pct=round(result.time_in_market_pct, 2),
        trades_per_day=round(result.trades_per_day, 2),
        trades_per_symbol_per_day=round(result.trades_per_symbol_per_day, 2),
        median_holding_time_minutes=round(result.median_holding_time_minutes, 1),
        commission_paid=round(result.commission_paid, 2),
        slippage_paid=round(result.slippage_paid, 2),
        total_cost_paid=round(result.total_cost_paid, 2),
        costs_as_pct_of_gross_pnl=round(result.costs_as_pct_of_gross_pnl, 2),
    )
