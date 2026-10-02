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
        "### 1.1 Strategy Variant Performance",
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
        "### 1.2 Trade-Frequency & Market Exposure Diagnostics",
        (
            "| Variant | Trades/Day | Trades/Sym/Day | Median Hold | "
            "Fills / Signals | Max Conc Pos | Re-entries | Time in Market % |"
        ),
        "|---|---|---|---|---|---|---|---|",
        (
            f"| `literal_clone` | {c.trades_per_day:.1f} | {c.trades_per_symbol_per_day:.2f} | "
            f"{c.median_holding_time_minutes:.1f}m | "
            f"{c.filled_entries_count} / {c.total_signals_generated} | "
            f"{c.max_simultaneous_positions} | {c.reentry_count} | {c.time_in_market_pct:.1f}% |"
        ),
        (
            f"| `risk_controlled` | {r.trades_per_day:.1f} | {r.trades_per_symbol_per_day:.2f} | "
            f"{r.median_holding_time_minutes:.1f}m | "
            f"{r.filled_entries_count} / {r.total_signals_generated} | "
            f"{r.max_simultaneous_positions} | {r.reentry_count} | {r.time_in_market_pct:.1f}% |"
        ),
        (
            f"| `regime_adapted` | {g.trades_per_day:.1f} | {g.trades_per_symbol_per_day:.2f} | "
            f"{g.median_holding_time_minutes:.1f}m | "
            f"{g.filled_entries_count} / {g.total_signals_generated} | "
            f"{g.max_simultaneous_positions} | {g.reentry_count} | {g.time_in_market_pct:.1f}% |"
        ),
        "",
        "### 1.3 Execution Cost & Financing Decomposition",
        "| Variant | Gross P&L | Commission | Slippage | Financing | Net P&L | Cost % of Gross |",
        "|---|---|---|---|---|---|---|",
        (
            f"| `literal_clone` | ${c.gross_pnl:,.2f} | ${c.commission_paid:,.2f} | "
            f"${c.slippage_paid:,.2f} | ${c.margin_interest_paid:,.2f} | "
            f"${c.net_pnl:,.2f} | {c.costs_as_pct_of_gross_pnl:.1f}% |"
        ),
        (
            f"| `risk_controlled` | ${r.gross_pnl:,.2f} | ${r.commission_paid:,.2f} | "
            f"${r.slippage_paid:,.2f} | ${r.margin_interest_paid:,.2f} | "
            f"${r.net_pnl:,.2f} | {r.costs_as_pct_of_gross_pnl:.1f}% |"
        ),
        (
            f"| `regime_adapted` | ${g.gross_pnl:,.2f} | ${g.commission_paid:,.2f} | "
            f"${g.slippage_paid:,.2f} | ${g.margin_interest_paid:,.2f} | "
            f"${g.net_pnl:,.2f} | {g.costs_as_pct_of_gross_pnl:.1f}% |"
        ),
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
    lines.append("")
    lines.append("## 4. Train / Validation / Test Out-of-Sample (OOS) Generalization Analysis")
    if comparison.oos_available:
        lines.extend(
            [
                (
                    "| Strategy Variant | Split Partition | Return % | Max DD % | Trades | "
                    "Win Rate | Profit Factor | Net P&L |"
                ),
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for variant_key in ["literal_clone", "risk_controlled", "regime_adapted"]:
            tr_m = comparison.train_metrics.get(variant_key)
            val_m = comparison.validation_metrics.get(variant_key)
            te_m = comparison.test_metrics.get(variant_key)
            if tr_m:
                lines.append(
                    f"| `{variant_key}` | Train | {tr_m.total_return_pct:.2f}% | "
                    f"{tr_m.max_drawdown_pct:.2f}% | {tr_m.total_trades} | "
                    f"{tr_m.win_rate * 100:.1f}% | {tr_m.profit_factor:.2f} | "
                    f"${tr_m.net_pnl:,.2f} |"
                )
            if val_m:
                lines.append(
                    f"| `{variant_key}` | Validation | {val_m.total_return_pct:.2f}% | "
                    f"{val_m.max_drawdown_pct:.2f}% | {val_m.total_trades} | "
                    f"{val_m.win_rate * 100:.1f}% | {val_m.profit_factor:.2f} | "
                    f"${val_m.net_pnl:,.2f} |"
                )
            if te_m:
                lines.append(
                    f"| `{variant_key}` | **Test (OOS)** | {te_m.total_return_pct:.2f}% | "
                    f"{te_m.max_drawdown_pct:.2f}% | {te_m.total_trades} | "
                    f"{te_m.win_rate * 100:.1f}% | {te_m.profit_factor:.2f} | "
                    f"${te_m.net_pnl:,.2f} |"
                )
    else:
        lines.extend(
            [
                "> **STATUS: UNAVAILABLE**",
                f"> {comparison.oos_status_reason or 'No OOS date boundaries provided.'}",
                "> *Untouched test evaluation requires explicit 'train_end', 'validation_end', "
                "and 'test_start' date boundaries.*",
            ]
        )

    # 5. Falsification & Robustness Diagnostics
    lines.extend(
        [
            "",
            "## 5. Falsification & Robustness Suite",
        ]
    )

    # 5.1 Benchmark Return Dependence Diagnostic
    if comparison.benchmark_bootstrap:
        bb = comparison.benchmark_bootstrap
        lines.extend(
            [
                "### 5.1 Benchmark Return Dependence Diagnostic (Politis & Romano 1994)",
                f"> **Diagnostic Scope:** `{bb.period_scope}` (Full Sample) | "
                f"**Resampling Unit:** `{bb.resampling_unit}` (`{bb.symbol}`) | "
                f"**Simulations:** 500 | "
                f"**Prob(Positive Return):** {bb.prob_positive * 100:.1f}%\n",
                "| Metric | Bootstrap Estimate |",
                "|---|---|",
                f"| Median Return | {bb.median_return_pct:.2f}% |",
                f"| Mean Return | {bb.mean_return_pct:.2f}% |",
                f"| 95% Confidence Interval | [{bb.ci_lower_pct:.2f}%, {bb.ci_upper_pct:.2f}%] |",
                "",
            ]
        )

    # 5.2 Strategy-Level Return Robustness Diagnostic
    if comparison.strategy_bootstrap:
        sb = comparison.strategy_bootstrap
        if sb.is_sufficient_sample:
            lines.extend(
                [
                    "### 5.2 Strategy-Level Return Robustness Diagnostic (Politis & Romano 1994)",
                    f"> **Diagnostic Scope:** `{sb.period_scope}` (Full Sample) | "
                    f"**Resampling Unit:** `{sb.resampling_unit}` | "
                    f"**Total Sessions:** {sb.sample_size} ({sb.active_trading_days} active, "
                    f"{sb.inactive_sessions} inactive) | "
                    f"**Prob(Positive Return):** {sb.prob_positive * 100:.1f}%\n",
                    f"> *Observation Definition: {sb.observation_definition}*\n",
                    "| Metric | Bootstrap Estimate |",
                    "|---|---|",
                    f"| Median Return | {sb.median_return_pct:.2f}% |",
                    f"| Mean Return | {sb.mean_return_pct:.2f}% |",
                    f"| 95% Confidence Interval | "
                    f"[{sb.ci_lower_pct:.2f}%, {sb.ci_upper_pct:.2f}%] |",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "### 5.2 Strategy-Level Return Robustness Diagnostic (Politis & Romano 1994)",
                    f"> **Diagnostic Scope:** `{sb.period_scope}` (Full Sample) | "
                    f"**Resampling Unit:** `{sb.resampling_unit}` | "
                    f"**Sample Status:** `INSUFFICIENT_SAMPLE` ({sb.insufficient_reason})",
                    f"> *Observation Definition: {sb.observation_definition}*",
                    "> *Diagnostic estimates withheld to prevent misleading numeric conclusions "
                    "on undersized sample.*",
                    "",
                ]
            )

    # 5.3 Final Out-of-Sample Strategy Robustness Diagnostic
    lines.append("### 5.3 Out-of-Sample Strategy Robustness (Untouched Test Period)")
    if comparison.oos_strategy_bootstrap:
        osb = comparison.oos_strategy_bootstrap
        if osb.is_sufficient_sample:
            lines.extend(
                [
                    f"> **Diagnostic Scope:** `{osb.period_scope}` (Untouched Test Partition) | "
                    f"**Resampling Unit:** `{osb.resampling_unit}` | "
                    f"**OOS Sessions:** {osb.sample_size} ({osb.active_trading_days} active, "
                    f"{osb.inactive_sessions} inactive) | "
                    f"**Prob(Positive Return):** {osb.prob_positive * 100:.1f}%\n",
                    f"> *Observation Definition: {osb.observation_definition}*\n",
                    "| Metric | Bootstrap Estimate |",
                    "|---|---|",
                    f"| Median Return | {osb.median_return_pct:.2f}% |",
                    f"| Mean Return | {osb.mean_return_pct:.2f}% |",
                    f"| 95% Confidence Interval | "
                    f"[{osb.ci_lower_pct:.2f}%, {osb.ci_upper_pct:.2f}%] |",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    f"> **Diagnostic Scope:** `{osb.period_scope}` (Untouched Test Partition) | "
                    f"> **OOS Robustness Status:** `INSUFFICIENT_SAMPLE` "
                    f"({osb.insufficient_reason})",
                    f"> *Observation Definition: {osb.observation_definition}*",
                    "> *Diagnostic estimates withheld to prevent misleading numeric conclusions "
                    "on undersized OOS sample.*",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "> **OOS Robustness Status:** `UNAVAILABLE` (No OOS test period configured)",
                "",
            ]
        )

    # 5.4 Leave-One-Out Ticker Exclusion
    if comparison.ticker_exclusion:
        te = comparison.ticker_exclusion
        lines.extend(
            [
                "### 5.4 Leave-One-Out Ticker Exclusion Test (Baseline: `risk_controlled`)",
                f"> **Diagnostic Scope:** `{te.period_scope}` ({te.scope_note}) | "
                f"**Dominant Ticker:** `{te.dominant_ticker or 'None'}` | "
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

    # 5.5 Strongest-Day Exclusion Diagnostic
    if comparison.strongest_day_exclusion:
        sd = comparison.strongest_day_exclusion
        lines.extend(
            [
                "### 5.5 Strongest-Day Exclusion Diagnostic (Attribution Test)",
                f"> **Diagnostic Scope:** `{sd.period_scope}` ({sd.scope_note})",
                "> *Note: This is an attribution diagnostic measuring whether positive expectancy "
                "relies entirely on a tiny handful of outlier days. It is NOT a strategy rerun.*\n",
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
            "## 6. Strategy Signal Semantics & Hypothesis Documentation",
            "| Rule / Component | `literal_clone` | `risk_controlled` | `regime_adapted` | "
            "Classification |",
            "|---|---|---|---|---|",
            "| **Sector Filter (`SMH`)** | Disabled | Disabled | Enabled (slope >= 0) | "
            "`HYPOTHESIS` |",
            "| **Pullback Trigger** | z <= -1.50 | z <= -1.50 | z <= -1.50 | `HYPOTHESIS` |",
            "| **Relative Volume Filter** | vol >= 0.70x | vol >= 0.70x | vol >= 0.70x | "
            "`HYPOTHESIS` |",
            "| **Exit Geometry** | Stored at entry | Stored at entry | Stored at entry | "
            "`ASSUMPTION` |",
            "| **Gross Leverage Limit** | 1.50x | 1.00x | 1.00x | `OBSERVED` / `HYPOTHESIS` |",
            "| **Layering Limit** | 2 layers max | 1 layer | 1 layer | `OBSERVED` / `HYPOTHESIS` |",
            "| **Max Symbol Weight** | 50% | 25% | 25% | `ASSUMPTION` |",
            "",
            "## 7. Options & Event Data Status",
            "- **Covered Calls:** `UNVALIDATED` (no tick-level historical option chains supplied).",
            "- **Event Blackouts:** `PARTIAL / UNVALIDATED` "
            "(no verified earnings calendar feed connected).",
            "",
            "## 8. Evidence Classification & Governance",
            "- `OBSERVED`: Reddit author reported $550k P&L on high-beta semi tickers with "
            "margin and covered calls.",
            "- `DERIVED`: High trade frequency and volatile names make transaction costs and "
            "slippage dominant P&L drivers.",
            "- `HYPOTHESIS`: Statistical pullback entries with ATR targets capture "
            "mean-reversion profits.",
            "- `ASSUMPTION`: Fixed slippage bps, conservative intrabar stop-first resolution, "
            "and entry-stored ATR geometry.",
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
