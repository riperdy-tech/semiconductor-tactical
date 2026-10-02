import argparse
from pathlib import Path

from tactical_engine.config import EngineConfig, load_config
from tactical_engine.data.models import Bar
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.options.chain_provider import OptionChainProvider
from tactical_engine.research.comparison import (
    StrategyComparisonResult,
    run_strategy_comparison,
)


def render_comparison_report(
    comparison: StrategyComparisonResult,
    config: EngineConfig,
) -> str:
    c = comparison.literal_clone
    r = comparison.risk_controlled
    g = comparison.regime_adapted

    lines = [
        "# Strategy Comparison Research Report",
        "",
        "## Executive Summary",
        "This report evaluates the three canonical variants of the tactical engine:",
        "1. `literal_clone`: Closest mechanical replication with layering and higher leverage.",
        "2. `risk_controlled`: Fixed risk budgets with strict position limits and stops.",
        "3. `regime_adapted`: Risk-controlled baseline with sector trend filtering.",
        "",
        "## 1. Strategy Variant Comparison",
        "| Variant | Return % | Max DD % | Trades | Win Rate | Profit Factor | Margin Calls |",
        "|---|---|---|---|---|---|---|",
        f"| `literal_clone` | {c.total_return_pct:.2f}% | {c.max_drawdown_pct:.2f}% | "
        f"{c.total_trades} | {c.win_rate * 100:.1f}% | {c.profit_factor:.2f} | "
        f"{c.margin_call_count} |",
        f"| `risk_controlled` | {r.total_return_pct:.2f}% | {r.max_drawdown_pct:.2f}% | "
        f"{r.total_trades} | {r.win_rate * 100:.1f}% | {r.profit_factor:.2f} | "
        f"{r.margin_call_count} |",
        f"| `regime_adapted` | {g.total_return_pct:.2f}% | {g.max_drawdown_pct:.2f}% | "
        f"{g.total_trades} | {g.win_rate * 100:.1f}% | {g.profit_factor:.2f} | "
        f"{g.margin_call_count} |",
        "",
        "## 2. Cost Sensitivity Analysis",
        "| Slippage | Return % | Max DD % | Cost Drag % | Net P&L |",
        "|---|---|---|---|---|",
    ]

    for slip_label, m in comparison.cost_sensitivity.items():
        lines.append(
            f"| {slip_label} | {m.total_return_pct:.2f}% | {m.max_drawdown_pct:.2f}% | "
            f"{m.cost_drag_pct:.1f}% | ${m.net_pnl:,.2f} |"
        )

    lines.extend(
        [
            "",
            "## 3. Leverage Sensitivity Analysis",
            "| Leverage Cap | Return % | Max DD % | Peak Margin Debt | Margin Interest |",
            "|---|---|---|---|---|",
        ]
    )

    for lev_label, m in comparison.leverage_sensitivity.items():
        lines.append(
            f"| {lev_label} | {m.total_return_pct:.2f}% | {m.max_drawdown_pct:.2f}% | "
            f"${m.peak_margin_debt:,.2f} | ${m.margin_interest_paid:,.2f} |"
        )

    # 4. Out-of-Sample Period Evaluation
    if comparison.oos_comparison:
        lines.extend(
            [
                "",
                "## 4. Out-of-Sample (OOS) Generalization Analysis",
                "| Period | Return % | Max DD % | Trades | Win Rate | Profit Factor | Net P&L |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for period_name, m in comparison.oos_comparison.items():
            lines.append(
                f"| `{period_name}` | {m.total_return_pct:.2f}% | {m.max_drawdown_pct:.2f}% | "
                f"{m.total_trades} | {m.win_rate * 100:.1f}% | {m.profit_factor:.2f} | "
                f"${m.net_pnl:,.2f} |"
            )

    # 5. Falsification & Robustness Diagnostics
    lines.extend(
        [
            "",
            "## 5. Falsification & Robustness Suite",
        ]
    )

    # 5.1 Stationary Block Bootstrap
    if comparison.block_bootstrap:
        bb = comparison.block_bootstrap
        lines.extend(
            [
                "### 5.1 Stationary Block Bootstrap (Autocorrelation-Preserving)",
                f"> **Expected Block Length:** 20 bars | **Simulations:** 500 | "
                f"**Prob(Positive Return):** {bb.prob_positive * 100:.1f}%\n",
                "| Metric | Bootstrap Estimate |",
                "|---|---|",
                f"| Median Return | {bb.median_return_pct:.2f}% |",
                f"| Mean Return | {bb.mean_return_pct:.2f}% |",
                f"| 95% Confidence Interval | [{bb.ci_lower_pct:.2f}%, {bb.ci_upper_pct:.2f}%] |",
                "",
            ]
        )

    # 5.2 Leave-One-Out Ticker Exclusion
    if comparison.ticker_exclusion:
        te = comparison.ticker_exclusion
        lines.extend(
            [
                "### 5.2 Leave-One-Out Ticker Exclusion Test",
                f"> **Dominant Ticker:** `{te.dominant_ticker or 'None'}` | "
                f"**Single-Ticker Fragile (>80% P&L):** "
                f"{'YES (Fragile)' if te.is_fragile_to_single_ticker else 'NO (Robust)'}\n",
                "| Excluded Ticker | Return % | Max DD % | Trades | Net P&L |",
                "|---|---|---|---|---|",
                f"| `None (Baseline)` | {te.baseline_metrics.total_return_pct:.2f}% | "
                f"{te.baseline_metrics.max_drawdown_pct:.2f}% | "
                f"{te.baseline_metrics.total_trades} | ${te.baseline_metrics.net_pnl:,.2f} |",
            ]
        )
        for sym, m in te.results_by_excluded_ticker.items():
            lines.append(
                f"| `Excluding {sym}` | {m.total_return_pct:.2f}% | {m.max_drawdown_pct:.2f}% | "
                f"{m.total_trades} | ${m.net_pnl:,.2f} |"
            )
        lines.append("")

    # 5.3 Strongest-Day Exclusion Diagnostic
    if comparison.strongest_day_exclusion:
        sd = comparison.strongest_day_exclusion
        lines.extend(
            [
                "### 5.3 Strongest-Day Exclusion Diagnostic (Attribution Test)",
                "> *Note: This is an attribution diagnostic measuring whether positive expectancy "
                "relies entirely on a tiny handful of outlier days.*\n",
                "| Scenario | Net P&L | Expectancy Positive? |",
                "|---|---|---|",
                f"| Full Baseline ({sd.total_trading_days} days) | ${sd.baseline_net_pnl:,.2f} | "
                f"{'YES' if sd.baseline_net_pnl > 0 else 'NO'} |",
                f"| Exclude Top 1 Day | ${sd.pnl_excluding_top_1:,.2f} | "
                f"{'YES' if sd.remains_positive_top_1 else 'NO'} |",
                f"| Exclude Top 3 Days | ${sd.pnl_excluding_top_3:,.2f} | "
                f"{'YES' if sd.remains_positive_top_3 else 'NO'} |",
                f"| Exclude Top 5 Days | ${sd.pnl_excluding_top_5:,.2f} | "
                f"{'YES' if sd.remains_positive_top_5 else 'NO'} |",
                "",
            ]
        )

    lines.extend(
        [
            "## 6. Options & Event Data Status",
            "- **Covered Calls:** `UNVALIDATED` (no tick-level historical option chains supplied).",
            "- **Event Blackouts:** `PARTIAL / UNVALIDATED` "
            "(no verified earnings calendar feed connected).",
            "",
            "## 7. Evidence Classification & Governance",

            "- `OBSERVED`: Reddit author reported $550k P&L on high-beta semi tickers with "
            "margin and covered calls.",
            "- `DERIVED`: High trade frequency and volatile names make transaction costs and "
            "slippage dominant P&L drivers.",
            "- `HYPOTHESIS`: Statistical pullback entries with ATR targets capture "
            "mean-reversion profits.",
            "- `ASSUMPTION`: Fixed slippage bps and conservative intrabar stop-first resolution.",
            "- `UNVERIFIED`: Option chain prices when simulated without tick-level historical "
            "option books.",
            "",
            "> [!IMPORTANT]",
            "> No edge can be claimed until parameter perturbations and untouched out-of-sample "
            "periods confirm persistent positive expectancy after all fees and financing costs.",
        ]
    )

    return "\n".join(lines)


def run_and_save_comparison_report(
    data: dict[str, list[Bar]],
    config: EngineConfig,
    option_chain_provider: OptionChainProvider | None = None,
    output_path: Path | str = "reports/strategy_comparison.md",
) -> str:
    comparison = run_strategy_comparison(data, config, option_chain_provider)
    report_md = render_comparison_report(comparison, config)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report_md, encoding="utf-8")
    return str(out_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run complete strategy comparison report")
    parser.add_argument(
        "--config", type=str, default="configs/base.yaml", help="Path to YAML config"
    )
    parser.add_argument("--bars", type=int, default=200, help="Number of bars per ticker")
    args = parser.parse_args()

    config = load_config(args.config)
    data = {
        sym: generate_synthetic_bars(
            symbol=sym, num_bars=args.bars, seed=config.project.random_seed + i
        )
        for i, sym in enumerate(config.strategy.universe)
    }

    report_path = run_and_save_comparison_report(data, config)
    print(f"Strategy comparison research report written to: {report_path}")


if __name__ == "__main__":
    main()
