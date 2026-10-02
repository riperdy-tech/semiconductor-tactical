from tactical_engine.reports.metrics import PerformanceMetrics
from tactical_engine.research.diagnostics import (
    calculate_stability_score,
    render_sweep_table,
)
from tactical_engine.research.sweeps import SweepResult


def test_calculate_stability_score():
    m1 = PerformanceMetrics(
        initial_cash=100000,
        final_equity=105000,
        total_return_pct=5.0,
        max_drawdown_pct=2.0,
        total_trades=10,
        win_rate=0.6,
        profit_factor=1.5,
        expectancy_per_trade=500,
        gross_pnl=5500,
        net_pnl=5000,
        cost_drag_pct=10,
    )
    m2 = PerformanceMetrics(
        initial_cash=100000,
        final_equity=104500,
        total_return_pct=4.5,
        max_drawdown_pct=2.2,
        total_trades=10,
        win_rate=0.6,
        profit_factor=1.4,
        expectancy_per_trade=450,
        gross_pnl=5000,
        net_pnl=4500,
        cost_drag_pct=10,
    )
    res1 = SweepResult(params={"zscore": -1.0}, metrics=m1)
    res2 = SweepResult(params={"zscore": -1.5}, metrics=m2)

    score = calculate_stability_score([res1, res2])
    assert 0.0 <= score <= 1.0

    table = render_sweep_table([res1, res2])
    assert "| Parameter Set | Return % | Max DD % | Trades | Win Rate |" in table
