from tactical_engine.backtest.manifest import RunManifest
from tactical_engine.reports.metrics import PerformanceMetrics


def render_markdown_report(
    metrics: PerformanceMetrics,
    manifest: RunManifest,
    ticker_attribution: dict[str, float],
) -> str:
    lines = [
        "# Tactical Research Engine — Backtest Report",
        "",
        "## Run Metadata",
        f"- **Run ID:** `{manifest.run_id}`",
        f"- **Git Commit:** `{manifest.git_commit}`",
        f"- **Config Hash:** `{manifest.config_hash}`",
        f"- **Strategy Variant:** `{manifest.strategy_variant}`",
        f"- **Symbols:** {', '.join(manifest.symbols)}",
        f"- **Timeframe:** `{manifest.timeframe}`",
        f"- **Timestamp (UTC):** `{manifest.created_at_utc}`",
        "",
        "## Performance Summary",
        "| Metric | Value |",
        "|---|---|",
        f"| Initial Capital | ${metrics.initial_cash:,.2f} |",
        f"| Final Equity | ${metrics.final_equity:,.2f} |",
        f"| Total Return | {metrics.total_return_pct:.2f}% |",
        f"| Max Drawdown | {metrics.max_drawdown_pct:.2f}% |",
        f"| Total Closed Trades | {metrics.total_trades} |",
        f"| Win Rate | {metrics.win_rate * 100:.2f}% |",
        f"| Profit Factor | {metrics.profit_factor:.2f} |",
        f"| Expectancy / Trade | ${metrics.expectancy_per_trade:,.2f} |",
        f"| Net P&L | ${metrics.net_pnl:,.2f} |",
        f"| Cost Drag | {metrics.cost_drag_pct:.2f}% |",
        "",
        "## Ticker P&L Attribution",
        "| Ticker | Net Realized P&L |",
        "|---|---|",
    ]
    for sym, pnl in ticker_attribution.items():
        lines.append(f"| {sym} | ${pnl:,.2f} |")

    lines.append("")
    lines.append("> [!NOTE]")
    lines.append(
        "> All metrics reflect deterministic execution under explicit cost and slippage models."
    )
    return "\n".join(lines)
