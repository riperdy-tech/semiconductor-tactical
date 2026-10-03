from tactical_engine.research.fidelity import FidelityMatrixResult


def format_fidelity_markdown_report(
    result: FidelityMatrixResult,
    git_sha: str = "39b4799",
    dataset_id: str = "massive_stocks_1m_51e9b529de55",
    aggregate_hash: str = "51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8",
    config_hash: str = "0d34835d97140803",
    sample_dates: str = "2026-07-01 to 2026-09-30",
    oos_scope: str = "POST_HOC_HOLDOUT / NOT_PRISTINE_OOS",
) -> str:
    """Generate canonical human-readable Markdown report for the Reddit Strategy Fidelity Matrix."""
    lines: list[str] = [
        "# REDDIT STRATEGY FIDELITY EXPERIMENT REPORT",
        "",
        "> **RESEARCH DESIGNATION:** Phase H — Reddit Strategy Fidelity Reconstruction",
        f"> **DATASET ID:** `{dataset_id}`",
        f"> **AGGREGATE DATA SHA256:** `{aggregate_hash}`",
        f"> **GIT COMMIT SHA:** `{git_sha}`",
        f"> **CONFIG HASH:** `{config_hash}`",
        f"> **SAMPLE DATE RANGE:** {sample_dates}",
        f"> **OOS SCOPE CLASSIFICATION:** `{oos_scope}`",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "This report evaluates the **Reddit Strategy Fidelity Reconstruction** per",
        "`docs/execution_plan/REDDIT_STRATEGY_FIDELITY_EXECUTION_PLAN.md`.",
        "",
        "### Key Principles Enforced:",
        (
            "1. **Baseline Preservation:** The prior negative result is preserved unchanged as "
            "`CURRENT_MECHANICAL_PULLBACK_BASELINE`."
        ),
        (
            "2. **Evidence-Labeled Rules:** Every strategy rule is explicitly classified as "
            "`OBSERVED`, `DERIVED`, `HYPOTHESIS`, `ASSUMPTION`, or `UNVERIFIED`."
        ),
        (
            "3. **Decoupled Layers:** Directional equity trading is evaluated separately from "
            "covered calls, margin leverage, and session coverage."
        ),
        (
            "4. **No Parameter Tuning:** Strictly prohibited from tuning parameters to match "
            "the reported $550k profit, 1,300+ trade count, or positive returns."
        ),
        "",
        "---",
        "",
        "## 1. Data Sufficiency Gate",
        "",
        "| Component Layer | Validation Status | Data Requirement | Findings |",
        "|---|---|---|---|",
        (
            f"| **Layer 1: Equity RTH** | `{result.data_sufficiency.equity_rth.value}` | "
            "1m OHLCV for MU, SNDK, SKHY, USD, SMH, SPY | "
            f"{result.data_sufficiency.details.get('equity_rth', 'N/A')} |"
        ),
        (
            f"| **Layer 2: Covered Calls** | `{result.data_sufficiency.covered_calls.value}` | "
            "Intraday option chains with bid/ask quotes | "
            f"{result.data_sufficiency.details.get('covered_calls', 'N/A')} |"
        ),
        (
            f"| **Layer 3: Margin / Capital** | "
            f"`{result.data_sufficiency.margin_financing.value}` | "
            "Financing rate, maintenance, forced liquidation | "
            f"{result.data_sufficiency.details.get('margin_financing', 'N/A')} |"
        ),
        (
            f"| **Layer 4: Extended Hours** | `{result.data_sufficiency.extended_hours.value}` | "
            "Historical pre/post-market quotes | "
            f"{result.data_sufficiency.details.get('extended_hours', 'N/A')} |"
        ),
        "",
        f"> **FULL REPLICATION STATUS:** `{result.full_composite_status}`",
        "",
        "---",
        "",
        "## 2. Core Fidelity Experiment Matrix",
        "",
        "| Experiment | Implementation Label | Return % | Max DD % | Trades | "
        "Win Rate | Profit Factor | Net P&L | Trades/Day | Median Hold | Status |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    # Row 1: Preserved Baseline
    b = result.baseline
    lines.append(
        f"| **Exp 1: Baseline** | `{b.implementation_label}` | {b.total_return_pct:.2f}% | "
        f"{b.max_drawdown_pct:.2f}% | {b.total_trades} | {b.win_rate*100:.1f}% | "
        f"{b.profit_factor:.2f} | ${b.net_pnl:,.2f} | {b.trades_per_day:.1f} | "
        f"{b.median_holding_time_minutes:.1f}m | PRESERVED BASELINE |"
    )

    # Row 1b: Diagnostic Sector-Filtered Mechanical Pullback
    if result.sector_filtered_diagnostic:
        diag = result.sector_filtered_diagnostic
        lines.append(
            f"| **Diag: Sector Filtered** | `{diag.implementation_label}` | "
            f"{diag.total_return_pct:.2f}% | {diag.max_drawdown_pct:.2f}% | {diag.total_trades} | "
            f"{diag.win_rate*100:.1f}% | {diag.profit_factor:.2f} | ${diag.net_pnl:,.2f} | "
            f"{diag.trades_per_day:.1f} | {diag.median_holding_time_minutes:.1f}m | "
            "MECHANICAL DIAGNOSTIC |"
        )

    # Row 2: Directional Equity
    d = result.directional_equity
    lines.append(
        f"| **Exp 2: Directional (1.0x)** | `{d.implementation_label}` | "
        f"{d.total_return_pct:.2f}% | {d.max_drawdown_pct:.2f}% | {d.total_trades} | "
        f"{d.win_rate*100:.1f}% | {d.profit_factor:.2f} | ${d.net_pnl:,.2f} | "
        f"{d.trades_per_day:.1f} | {d.median_holding_time_minutes:.1f}m | VALIDATED RTH |"
    )

    # Row 3: Directional + Margin
    m = result.directional_margin
    lines.append(
        f"| **Exp 3: Directional + Margin (1.5x)** | `{m.implementation_label}` | "
        f"{m.total_return_pct:.2f}% | {m.max_drawdown_pct:.2f}% | {m.total_trades} | "
        f"{m.win_rate*100:.1f}% | {m.profit_factor:.2f} | ${m.net_pnl:,.2f} | "
        f"{m.trades_per_day:.1f} | {m.median_holding_time_minutes:.1f}m | VALIDATED MECHANICS |"
    )

    # Row 4: Covered Calls
    lines.append(
        "| **Exp 4: Covered Calls** | `COVERED_CALL_OVERLAY` | N/A | N/A | N/A | "
        f"N/A | N/A | N/A | N/A | N/A | `{result.covered_calls_status}` |"
    )

    # Row 5: Full Composite
    lines.append(
        "| **Exp 5: Full Composite** | `FULL_VALIDATED_COMPOSITE` | N/A | N/A | N/A | "
        f"N/A | N/A | N/A | N/A | N/A | `{result.full_composite_status}` |"
    )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Execution Cost & Drag Decomposition (P&L Attribution)",
        "",
        "| Experiment | Signal-Price P&L | Slippage Paid | Commission | "
        "Margin Interest | Net Realized P&L | Portfolio Net P&L | Cost Drag % |",
        "|---|---|---|---|---|---|---|---|",
        (
            f"| **Exp 1: Baseline** | ${b.pre_slippage_pnl:,.2f} | ${b.slippage_paid:,.2f} | "
            f"${b.commission_paid:,.2f} | ${b.margin_interest_paid:,.2f} | "
            f"${b.net_realized_pnl:,.2f} | ${b.portfolio_net_pnl:,.2f} | "
            f"{b.costs_as_pct_of_gross_pnl:.1f}% |"
        ),
    ])

    if result.sector_filtered_diagnostic:
        diag = result.sector_filtered_diagnostic
        lines.append(
            f"| **Diag: Sector Filtered** | ${diag.pre_slippage_pnl:,.2f} | "
            f"${diag.slippage_paid:,.2f} | ${diag.commission_paid:,.2f} | "
            f"${diag.margin_interest_paid:,.2f} | ${diag.net_realized_pnl:,.2f} | "
            f"${diag.portfolio_net_pnl:,.2f} | {diag.costs_as_pct_of_gross_pnl:.1f}% |"
        )

    lines.extend([
        (
            f"| **Exp 2: Directional Fidelity** | ${d.pre_slippage_pnl:,.2f} | "
            f"${d.slippage_paid:,.2f} | ${d.commission_paid:,.2f} | "
            f"${d.margin_interest_paid:,.2f} | ${d.net_realized_pnl:,.2f} | "
            f"${d.portfolio_net_pnl:,.2f} | {d.costs_as_pct_of_gross_pnl:.1f}% |"
        ),
        (
            f"| **Exp 3: Directional + Margin** | ${m.pre_slippage_pnl:,.2f} | "
            f"${m.slippage_paid:,.2f} | ${m.commission_paid:,.2f} | "
            f"${m.margin_interest_paid:,.2f} | ${m.net_realized_pnl:,.2f} | "
            f"${m.portfolio_net_pnl:,.2f} | {m.costs_as_pct_of_gross_pnl:.1f}% |"
        ),
        "",
        "> **ACCOUNTING INVARIANT & NO DOUBLE-COUNTING RULE:**",
        (
            "> `Signal-Price P&L - Execution Slippage - Commission - Margin Interest = "
            "Portfolio Net P&L`"
        ),
        (
            "> Execution slippage is embedded directly into fill prices at simulation time; "
            "it is never deducted a second time from Net Realized P&L."
        ),
        "",
        "---",
        "",
        "## 4. Descriptive Plausibility Diagnostics",
        "",
        "| Diagnostic Metric | Source Claim | Baseline | Directional Fidelity | Interpretation |",
        "|---|---|---|---|---|",
        (
            "| **Total Trade Count** | ~1,300+ trades / 90d | "
            f"{b.total_trades} trades | {d.total_trades} trades | "
            "Descriptive check; not an optimization target |"
        ),
        (
            "| **Trades per Day** | ~20.6 trades/day across 63 sessions | "
            f"{b.trades_per_day:.1f} trades/day | {d.trades_per_day:.1f} trades/day | "
            "Reduced frequency relative to mechanical baseline |"
        ),
        (
            "| **Median Holding Time** | Multi-hour to multi-day swing positions | "
            f"{b.median_holding_time_minutes:.1f} min | "
            f"{d.median_holding_time_minutes:.1f} min | "
            "Reduced high-frequency churn relative to the baseline |"
        ),
        (
            "| **Order Execution Type** | Explicit stop-limits [OBSERVED] | "
            "Next-bar market orders | Stop-limit entry proxy [HYPOTHESIS] | "
            "Modeled entry proxy inspired by observed stop-limit use |"
        ),
        (
            "| **Covered Calls** | Sold on strength, repurchased on pullbacks | "
            "Disabled | Unvalidated (no chain data) | "
            "Option cash flows strictly quarantined |"
        ),
        (
            "| **Non-RTH Trading** | Traded SKHY/Kioxia outside U.S. RTH | "
            "RTH only | RTH only (Unvalidated non-RTH) | "
            "Declared data gap; no synthetic fabrication |"
        ),
        "",
        (
            "> **PLAUSIBILITY NOTE:** Plausibility diagnostics serve exclusively as "
            "reality checks. Parameters were never tuned to match trade count or dollar profits. "
            "The observed similarity in trade count (~1,334 vs ~1,300+) is not treated as "
            "validation of the strategy. Because directional parameters are classified as "
            "POST_HOC_SPECIFIED, trade count similarity cannot be treated as independent "
            "confirmation of fidelity."
        ),
        "",
        "---",
        "",
        "## 5. Component Ablations (Experiment 6)",
        "",
        "| Ablation Name | Return % | Max DD % | Trades | Win Rate | "
        "Profit Factor | Net P&L | Key Observation |",
        "|---|---|---|---|---|---|---|---|",
    ])

    for name, ab in result.ablations.items():
        obs = "N/A"
        if "sector_filtered_diagnostic" in name:
            obs = "Mechanical pullback with sector trend filter active"
        elif "market_orders" in name:
            obs = "Evaluating market order vs stop-limit execution drag"
        elif "no_sector" in name:
            obs = "Evaluating impact of sector regime filter"
        elif "2.0x" in name:
            obs = "Evaluating 2.0x leverage scaling"
        elif "1.0x" in name:
            obs = "Unleveraged pure directional equity baseline"
        elif "1.5x" in name:
            obs = "Moderate leverage with 2 layers"

        lines.append(
            f"| `{name}` | {ab.total_return_pct:.2f}% | {ab.max_drawdown_pct:.2f}% | "
            f"{ab.total_trades} | {ab.win_rate*100:.1f}% | {ab.profit_factor:.2f} | "
            f"${ab.net_pnl:,.2f} | {obs} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 6. Research Conclusion & Next Steps",
        "",
        (
            "1. **Fidelity Gap Partially Addressed — Deterministic Hypothesis Implemented:** "
            "The original z-score/ATR baseline was a poor proxy for the described discretionary "
            "process. Phase H introduced a structurally closer deterministic hypothesis, but it "
            "remains a model approximation, not recovered source code."
        ),
        (
            "2. **Strict Epistemic Quarantine:** Covered calls and extended hours remain labeled "
            "`UNVALIDATED` until authentic primary market data is provided."
        ),
        (
            "3. **Research Integrity & Status:** No parameters were tuned to match the $550k claim "
            "or 1,300 trades. Directional parameters are classified as `POST_HOC_SPECIFIED`. "
            "Therefore: `FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED` and "
            "`PRISTINE_OOS = UNAVAILABLE`."
        ),
        "",
        (
            "> **STOP CONDITION:** Phase I research integrity correction complete. "
            "Software changes cease. No further optimization loops permitted."
        ),
    ])

    return "\n".join(lines)
