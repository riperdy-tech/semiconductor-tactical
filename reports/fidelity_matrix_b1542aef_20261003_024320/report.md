# REDDIT STRATEGY FIDELITY EXPERIMENT REPORT

> **RESEARCH DESIGNATION:** Phase H — Reddit Strategy Fidelity Reconstruction
> **DATASET ID:** `massive_stocks_1m_51e9b529de55`
> **AGGREGATE DATA SHA256:** `51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8`
> **GIT COMMIT SHA:** `981232a`
> **CONFIG HASH:** `0d34835d97140803`
> **SAMPLE DATE RANGE:** 2026-07-01T00:00:00Z to 2026-09-30T23:59:59Z
> **OOS SCOPE CLASSIFICATION:** `POST_HOC_HOLDOUT / NOT_PRISTINE_OOS`

---

## Executive Summary

This report evaluates the **Reddit Strategy Fidelity Reconstruction** per
`docs/execution_plan/REDDIT_STRATEGY_FIDELITY_EXECUTION_PLAN.md`.

### Key Principles Enforced:
1. **Baseline Preservation:** The prior negative result is preserved unchanged as `CURRENT_MECHANICAL_PULLBACK_BASELINE`.
2. **Evidence-Labeled Rules:** Every strategy rule is explicitly classified as `OBSERVED`, `DERIVED`, `HYPOTHESIS`, `ASSUMPTION`, or `UNVERIFIED`.
3. **Decoupled Layers:** Directional equity trading is evaluated separately from covered calls, margin leverage, and session coverage.
4. **No Parameter Tuning:** Strictly prohibited from tuning parameters to match the reported $550k profit, 1,300+ trade count, or positive returns.

---

## 1. Data Sufficiency Gate

| Component Layer | Validation Status | Data Requirement | Findings |
|---|---|---|---|
| **Layer 1: Equity RTH** | `VALIDATED` | 1m OHLCV for MU, SNDK, SKHY, USD, SMH, SPY | 1-minute U.S. regular trading hours (09:30-16:00 ET) verified market data available for core semiconductor universe and benchmarks. |
| **Layer 2: Covered Calls** | `UNVALIDATED` | Intraday option chains with bid/ask quotes | UNVALIDATED: Historical option chain tick/minute data (contract, timestamp, bid, ask, strike, expiration) is unavailable. Per AGENTS.md Rule 7, theoretical Black-Scholes pricing cannot be substituted for real market execution. Covered calls remain UNVALIDATED. |
| **Layer 3: Margin / Capital** | `VALIDATED` | Financing rate, maintenance, forced liquidation | VALIDATED MECHANICS: Margin interest accrual, maintenance requirement calculations, and forced liquidation orders are fully implemented and verified in the simulation engine. Specific leverage levels remain parameterized ASSUMPTIONS. |
| **Layer 4: Extended Hours** | `UNVALIDATED` | Historical pre/post-market quotes | UNVALIDATED: Current dataset is strictly filtered to U.S. regular trading hours (09:30-16:00 ET). No historical pre-market, post-market, or foreign venue (KRX: 000660) data is available. Per AGENTS.md, non-RTH trading is marked UNVALIDATED. |

> **FULL REPLICATION STATUS:** `BLOCKED_BY_DATA_GATE (Extended-hours and option chain data unvalidated)`

---

## 2. Core Fidelity Experiment Matrix

| Experiment | Implementation Label | Return % | Max DD % | Trades | Win Rate | Profit Factor | Net P&L | Trades/Day | Median Hold | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| **Exp 1: Baseline** | `CURRENT_MECHANICAL_PULLBACK_BASELINE` | -92.89% | 92.89% | 5082 | 31.8% | 0.28 | $-92,887.16 | 79.4 | 2.0m | PRESERVED BASELINE |
| **Diag: Sector Filtered** | `MECHANICAL_PULLBACK_SECTOR_FILTERED_DIAGNOSTIC` | -34.88% | 35.10% | 1114 | 28.8% | 0.32 | $-34,919.97 | 17.4 | 2.0m | MECHANICAL DIAGNOSTIC |
| **Exp 2: Directional (1.0x)** | `DIRECTIONAL_FIDELITY_RECONSTRUCTION` | -53.27% | 53.50% | 1334 | 29.2% | 0.55 | $-53,264.77 | 20.8 | 8.0m | VALIDATED RTH |
| **Exp 3: Directional + Margin (1.5x)** | `DIRECTIONAL_FIDELITY_RECONSTRUCTION` | -58.51% | 58.72% | 1369 | 28.1% | 0.53 | $-58,507.64 | 21.4 | 8.0m | VALIDATED MECHANICS |
| **Exp 4: Covered Calls** | `COVERED_CALL_OVERLAY` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | `UNVALIDATED (Historical option chain quotes absent)` |
| **Exp 5: Full Composite** | `FULL_VALIDATED_COMPOSITE` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | `BLOCKED_BY_DATA_GATE (Extended-hours and option chain data unvalidated)` |

---

## 3. Execution Cost & Drag Decomposition (P&L Attribution)

| Experiment | Signal-Price P&L | Slippage Paid | Commission | Margin Interest | Net Realized P&L | Portfolio Net P&L | Cost Drag % |
|---|---|---|---|---|---|---|---|
| **Exp 1: Baseline** | $-7,889.08 | $84,998.08 | $0.00 | $0.04 | $-92,887.16 | $-92,887.20 | 91.5% |
| **Diag: Sector Filtered** | $1,664.97 | $36,584.94 | $0.00 | $0.01 | $-34,919.97 | $-34,919.98 | 104.8% |
| **Exp 2: Directional Fidelity** | $-1,693.53 | $51,571.24 | $0.00 | $0.07 | $-53,264.77 | $-53,264.84 | 96.8% |
| **Exp 3: Directional + Margin** | $-1,882.40 | $56,625.24 | $0.00 | $0.40 | $-58,507.64 | $-58,508.04 | 96.8% |

> **ACCOUNTING INVARIANT & NO DOUBLE-COUNTING RULE:**
> `Signal-Price P&L - Execution Slippage - Commission - Margin Interest = Portfolio Net P&L`
> Execution slippage is embedded directly into fill prices at simulation time; it is never deducted a second time from Net Realized P&L.

---

## 4. Descriptive Plausibility Diagnostics

| Diagnostic Metric | Source Claim | Baseline | Directional Fidelity | Interpretation |
|---|---|---|---|---|
| **Total Trade Count** | ~1,300+ trades / 90d | 5082 trades | 1334 trades | Descriptive check; not an optimization target |
| **Trades per Day** | ~20.6 trades/day across 63 sessions | 79.4 trades/day | 20.8 trades/day | Reduced frequency relative to mechanical baseline |
| **Median Holding Time** | Multi-hour to multi-day swing positions | 2.0 min | 8.0 min | Reduced high-frequency churn relative to the baseline |
| **Order Execution Type** | Explicit stop-limits [OBSERVED] | Next-bar market orders | Stop-limit entry proxy [HYPOTHESIS] | Modeled entry proxy inspired by observed stop-limit use |
| **Covered Calls** | Sold on strength, repurchased on pullbacks | Disabled | Unvalidated (no chain data) | Option cash flows strictly quarantined |
| **Non-RTH Trading** | Traded SKHY/Kioxia outside U.S. RTH | RTH only | RTH only (Unvalidated non-RTH) | Declared data gap; no synthetic fabrication |

> **PLAUSIBILITY NOTE:** Plausibility diagnostics serve exclusively as reality checks. Parameters were never tuned to match trade count or dollar profits. The observed similarity in trade count (~1,334 vs ~1,300+) is not treated as validation of the strategy. Because directional parameters are classified as POST_HOC_SPECIFIED, trade count similarity cannot be treated as independent confirmation of fidelity.

---

## 5. Component Ablations (Experiment 6)

| Ablation Name | Return % | Max DD % | Trades | Win Rate | Profit Factor | Net P&L | Key Observation |
|---|---|---|---|---|---|---|---|
| `mechanical_pullback_sector_filtered_diagnostic` | -34.88% | 35.10% | 1114 | 28.8% | 0.32 | $-34,919.97 | Mechanical pullback with sector trend filter active |
| `equity_only_1.0x` | -53.27% | 53.50% | 1334 | 29.2% | 0.55 | $-53,264.77 | Unleveraged pure directional equity baseline |
| `equity_plus_margin_1.5x` | -58.51% | 58.72% | 1369 | 28.1% | 0.53 | $-58,507.64 | Moderate leverage with 2 layers |
| `equity_plus_margin_2.0x` | -58.46% | 58.67% | 1370 | 28.2% | 0.53 | $-58,461.96 | Evaluating 2.0x leverage scaling |
| `directional_market_orders` | -54.54% | 54.77% | 1427 | 27.1% | 0.54 | $-54,539.01 | Evaluating market order vs stop-limit execution drag |
| `directional_no_sector_filter` | -59.77% | 60.00% | 1658 | 28.1% | 0.55 | $-59,766.66 | Evaluating impact of sector regime filter |

---

## 6. Research Conclusion & Next Steps

1. **Fidelity Gap Partially Addressed — Deterministic Hypothesis Implemented:** The original z-score/ATR baseline was a poor proxy for the described discretionary process. Phase H introduced a structurally closer deterministic hypothesis, but it remains a model approximation, not recovered source code.
2. **Strict Epistemic Quarantine:** Covered calls and extended hours remain labeled `UNVALIDATED` until authentic primary market data is provided.
3. **Research Integrity & Status:** No parameters were tuned to match the $550k claim or 1,300 trades. Directional parameters are classified as `POST_HOC_SPECIFIED`. Therefore: `FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED` and `PRISTINE_OOS = UNAVAILABLE`.

> **STOP CONDITION:** Phase I research integrity correction complete. Software changes cease. No further optimization loops permitted.