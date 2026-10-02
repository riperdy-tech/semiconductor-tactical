from tactical_engine.backtest.manifest import RunManifest
from tactical_engine.reports.metrics import PerformanceMetrics
from tactical_engine.reports.renderer import render_markdown_report


def test_markdown_report_rendering():
    manifest = RunManifest(
        config_hash="abc1234",
        strategy_variant="risk_controlled",
        symbols=["MU"],
        timeframe="1m",
        random_seed=42,
    )
    metrics = PerformanceMetrics(
        initial_cash=100000.0,
        final_equity=105000.0,
        total_return_pct=5.0,
        max_drawdown_pct=2.1,
        total_trades=10,
        win_rate=0.6,
        profit_factor=1.8,
        expectancy_per_trade=500.0,
        gross_pnl=5500.0,
        net_pnl=5000.0,
        cost_drag_pct=9.1,
    )
    report = render_markdown_report(metrics, manifest, {"MU": 5000.0})
    assert "# Tactical Research Engine — Backtest Report" in report
    assert "risk_controlled" in report
    assert "5.00%" in report
