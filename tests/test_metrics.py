from datetime import datetime, timezone
from tactical_engine.backtest.engine import BacktestResult
from tactical_engine.backtest.state import TradeRecord
from tactical_engine.reports.metrics import calculate_metrics


def test_performance_metrics_calculation():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 5, 15, 30, tzinfo=timezone.utc)
    result = BacktestResult(
        initial_cash=100_000.0,
        final_equity=105_000.0,
        total_trades=2,
        trades=[
            TradeRecord(
                symbol="MU",
                entry_time=t0,
                exit_time=t1,
                entry_price=100.0,
                exit_price=106.0,
                quantity=100.0,
                gross_pnl=600.0,
                net_pnl=590.0,
                exit_reason="target_hit",
            ),
            TradeRecord(
                symbol="MU",
                entry_time=t0,
                exit_time=t1,
                entry_price=100.0,
                exit_price=98.0,
                quantity=100.0,
                gross_pnl=-200.0,
                net_pnl=-210.0,
                exit_reason="stop_loss_hit",
            ),
        ],
        equity_curve=[100_000.0, 102_000.0, 99_000.0, 105_000.0],
        timestamps=["2026-01-05T14:30:00Z", "2026-01-05T14:31:00Z", "2026-01-05T14:32:00Z", "2026-01-05T14:33:00Z"],
    )
    metrics = calculate_metrics(result)
    assert metrics.total_return_pct == 5.0
    assert metrics.win_rate == 0.5
    assert metrics.profit_factor > 1.0
    assert metrics.max_drawdown_pct > 0.0
