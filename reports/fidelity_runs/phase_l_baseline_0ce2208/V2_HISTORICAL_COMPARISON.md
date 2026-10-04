# Reddit Behavioral Replication V2 — Historical Comparison Report

**Run ID:** `bc19e12e`  
**Date Generated:** `2026-10-04T02:04:12.997367+00:00`  
**Git Commit SHA:** `dce8ac4`  
**Dataset ID:** `massive_stocks_1m_51e9b529de55`  
**Dataset SHA256:** `51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8`  
**Nominal Date Range:** `2026-07-01T00:00:00Z to 2026-09-30T23:59:59Z`  
**Effective Evaluation Start:** `2026-07-13T13:30:00+00:00`  
**Evaluation Status:** `POST_HOC_HOLDOUT / NOT_PRISTINE_OOS`  
**Phase L Accounting Status:** `PHASE_L_ACCOUNTING_CORRECTED`  
**Preserved Phase K Baseline:** Run ID `5080f859` (Commit `1eda7cc`) preserved at `reports/fidelity_runs/phase_k_baseline_1eda7cc/`  

---

## 1. Research Scope & Mandatory Epistemic Gates

```text
FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED
DIRECT_ASIA_REPLICATION_STATUS    = OUT_OF_SCOPE_FOR_V2
TRUE_LEVEL2_REPLICATION          = UNVALIDATED
HISTORICAL_OPTION_CHAIN_STATUS   = UNVALIDATED
PRISTINE_OOS                     = UNAVAILABLE
```

> [!IMPORTANT]
> **Phase L Scope Boundaries & Operational Constraints:**
> 1. **U.S.-Market Only Scope:** Direct execution on KRX (000660) and Tokyo (6736) is strictly out of scope.
> 2. **Clean Headline Universe:** Evaluated strictly on `MU`, `SNDK`, and `SKHY`.
> 3. **Excluded Proxies:** Generic `USD` ETF, candidate 2x ETFs (SKUU, SKHU, SKHL, MUU, SNDG, SNDU, SNXX), and `KXIAY` OTC ADR.
> 4. **Effective Common Start Audit:** Evaluation commences strictly at `2026-07-13T13:30:00Z` (first common 3-asset bar; 22,230 1m bars). The pre-core interval (July 1 to July 10, 2,730 bars) is classified as `UNINITIALIZED / NOT_IN_SAMPLE` because SKHY was not available. No tactical trading is permitted before core portfolio establishment.
> 5. **Exogenous Core Initialization:** 60% core is established at effective start open prices ($59,223.68 starting core value = 59.22% actual allocation; $40,776.32 residual tactical cash) with zero commissions and zero slippage charged to initial state setup.
> 6. **Zero Parameter Tuning:** Directional parameters remain frozen identically to Phase K; no optimization or parameter sweeps performed.

---

## 2. Phase K Baseline vs Phase L Corrected Reconciliation

| Evaluation Dimension | Phase K Baseline (`1eda7cc`) | Phase L Corrected Result | Variance / Audit Explanation |
|---|---|---|---|
| **Evaluation Start** | `2026-07-01T00:00:00Z` (Nominal) | `2026-07-13T13:30:00Z` (Effective Common) | Pre-core July 1–10 interval excluded as `UNINITIALIZED` (SKHY start disparity) |
| **Evaluation Bars** | 24,960 bars (MU/SNDK) / 22,230 (SKHY) | 22,230 bars (All 3 symbols) | Eliminates pre-core tactical trading prior to SKHY availability |
| **Starting Core Value** | $59,837.19 (Nominal setup) | $59,223.68 (Exogenous, 0 cost) | Zero slippage/commissions charged to initial baseline portfolio |
| **Starting Tactical Cash** | $40,162.81 | $40,776.32 | Residual cash after integer-share allocation (59.22% core / 40.78% cash) |
| **V2-A: Core Only Return** | +6.48% | **+6.48%** | Core holding path identical (+6.48%); ending core value $65,705.84 |
| **V2-B: Core + Tactical Return** | +7.38% | **+7.93%** | +0.55% spread uplift due to removing pre-core trading losses |
| **V2-C: Core + Tactical + Margin** | +7.38% | **+7.93%** | Identical to V2-B (+7.93%); margin capability unexercised |
| **Tactical Net Contribution** | +0.90% (+$900.00) | **+1.45% (+$1,446.69)** | Uplift from removing pre-core uninitialized trading (-$2,500+ pre-core loss) |
| **Completed Round Trips (V2-B)** | 123 trades | 108 trades | 15 pre-core trades (July 1–10) properly excluded from common evaluation |
| **Peak Margin Debt (V2-C)** | $0.00 | $0.00 | Tactical cash sleeve funded all positions without margin borrowing |
| **Total Margin Interest (V2-C)** | $0.00 | $0.00 | Zero financing interest incurred historically |
| **Margin Status (V2-C)** | NOT EXERCISED HISTORICALLY | CAPABILITY PRESENT / NOT EXERCISED HISTORICALLY | Zero historical margin usage; capability verified via synthetic test |
| **Pre-Slippage P&L Semantics** | Calculated from fill prices | Calculated from reference prices | Satisfies exact invariant: `pre_slippage_pnl - slippage == realized_pnl` |
| **Execution Buying Power Check** | Lookahead (used bar close) | No lookahead (uses bar open) | Valued at execution time open prices prior to fill execution |
| **Margin Liquidation Timing** | Same-bar close execution | Queued for next-bar open | No lookahead same-bar execution |

> [!NOTE]
> **Why Phase L Changed Ending Equity (+7.38% -> ++7.93%):**  
> In Phase K, backtest ran from July 1, but SKHY data did not start until July 13. During July 1–10, 15 trades were executed on MU and SNDK before the core was established, incurring over -$2,500 in losses. Properly aligning the common evaluation window to `2026-07-13T13:30:00Z` (when all three symbols exist) removes this uninitialized pre-core artifact. Core return (+6.48%) remained identical because core was always established on July 13. Parameters were NOT tuned.

---

## 3. Comparative Performance Matrix (V2-A, V2-B, V2-C)

| Performance & Risk Metric | V2-A: Core Only | V2-B: Core + Tactical | V2-C: Core + Tactical + Margin |
|---|---|---|---|
| **Strategy Description** | 60% Static Core | Core + Tactical (Cash) | Core + Tactical + Margin (2.0x) |
| **Initial Cash** | $100,000.00 | $100,000.00 | $100,000.00 |
| **Effective Start Timestamp** | 2026-07-13T13:30:00+00:00 | 2026-07-13T13:30:00+00:00 | 2026-07-13T13:30:00+00:00 |
| **Evaluation End Timestamp** | 2026-09-30T19:59:00+00:00 | 2026-09-30T19:59:00+00:00 | 2026-09-30T19:59:00+00:00 |
| **Starting Core Value** | $59,223.68 (59.22%) | $59,223.68 (59.22%) | $59,223.68 (59.22%) |
| **Residual Tactical Cash** | $40,776.32 | $40,776.32 | $40,776.32 |
| **Final Net Equity** | $106,482.16 | $107,928.85 | $107,928.85 |
| **Total Net P&L** | $+6,482.16 | $+7,928.85 | $+7,928.85 |
| **Total Net Return (%)** | **+6.48%** | **+7.93%** | **+7.93%** |
| **Maximum Drawdown (%)** | 20.82% | 23.06% | 23.06% |
| **Core Realized P&L** | $0.00 | $0.00 | $0.00 |
| **Core Unrealized P&L** | $+6,482.16 | $+6,482.16 | $+6,482.16 |
| **Tactical Closed Realized P&L** | $0.00 | $-3,830.14 | $-3,830.14 |
| **Tactical Terminal Unrealized P&L** | $0.00 | $+5,276.83 | $+5,276.83 |
| **Tactical Economic Contribution** | $0.00 (Benchmark) | $+1,446.69 | $+1,446.69 |
| **Signals Generated Count** | 0 | 168 | 168 |
| **Order Attempts Count** | 0 | 168 | 168 |
| **Entry Fills Count** | 0 | 57 | 57 |
| **Reload Fills Count** | 0 | 28 | 28 |
| **Partial Exit Fills Count** | 0 | 29 | 29 |
| **Full Exit Fills Count** | 0 | 54 | 54 |
| **Completed FIFO Round Trips** | 0 | 108 | 108 |
| **Ending Open Tactical Lots** | 0 | 6 | 6 |
| **Ending Open Tactical Shares** | 0 | 79 | 79 |
| **Tactical Win Rate (%)** | N/A | 32.4% | 32.4% |
| **Median Holding Time** | N/A | 17.0 min | 17.0 min |
| **Margin Capability Status** | N/A (Unlevered) | Unlevered (Cash) | CAPABILITY PRESENT / NOT EXERCISED HISTORICALLY |
| **Peak Margin Debt** | $0.00 | $0.00 | $0.00 |
| **Margin Interest Paid** | $0.00 | $0.00 | $0.00 |
| **Margin Calls / Liquidations** | 0 / 0 | 0 / 0 | 0 / 0 |
| **Gross Reference P&L (Pre-Slippage)** | $0.00 | $-3,185.67 | $-3,185.67 |
| **Slippage Paid** | $0.00 | $659.07 | $659.07 |
| **Commissions Paid** | $0.00 | $0.00 | $0.00 |
| **Net Realized Trade P&L** | $0.00 | $-3,830.14 | $-3,830.14 |
| **Accounting Invariant Check** | Clean (`True`) | Clean (`True`) | Clean (`True`) |

---

## 4. Layered Accounting Invariant Reconciliation

Every dollar of performance is reconciled across four distinct non-overlapping layers:

### A. Tactical Closed Round-Trip Layer
```text
Gross Reference Trade P&L (Ref Prices):  $-3,185.67
Less Execution Slippage:                -$659.07
Less Brokerage Commissions:             -$0.00
-------------------------------------------------------------------------
Net Realized Closed Tactical P&L:       $-3,830.14
```

### B. Terminal Mark-to-Market Layer
```text
Ending Open Tactical Lots MTM:          $+5,276.83
Persistent Core Holdings MTM:           $+6,482.16
-------------------------------------------------------------------------
Total Terminal Unrealized P&L:          $+11,758.99
```

### C. Financing & Account Balance Layer
```text
Net Realized Tactical P&L:              $-3,830.14
Plus Terminal Unrealized P&L:           $+11,758.99
Less Financing Margin Interest:         -$0.00
-------------------------------------------------------------------------
Calculated Total Net Strategy P&L:      $+7,928.85
Ending Equity minus Initial Cash:       $+7,928.85
Reconciliation Discrepancy:             $0.000000
Invariant Status:                       Clean (True)
```

---

## 5. Component Attribution Analysis

### Key Findings:
1. **Core Static Holding (V2-A):** Delivered **+6.48%** return ($+6,482.16 net P&L) across July 13–Sept 30, with max drawdown of 20.82%. Core shares were never sold or contaminated.
2. **Tactical Sleeve Uplift (V2-B vs V2-A):** Added **+1.45%** net return spread ($+1,446.69 net tactical contribution). Win rate 32.4% with median hold 17.0m across 108 completed FIFO round trips.
3. **Margin Capability Impact (V2-C vs V2-B):** Margin capability was active but unexercised historically because the $40,776.32 tactical cash sleeve funded all 108 positions without borrowing. Peak margin debt was $0.00; margin interest was $0.00. Margin calls/liquidations were 0.
4. **Synthetic Margin Capability Validation:** A separate synthetic test (`test_v2_c_margin_activation_synthetic`) verifies that under forced severe cash constraints, margin debt, interest accrual, maintenance constraints, and tactical-first liquidation execute deterministically.
5. **Core Isolation Integrity:** Persistent core inventory remained 100% isolated from tactical stop and profit exits across all 22,230 bars.

---

## 6. Research Integrity & Blocker Assessment

- **Parameters Frozen:** No signal parameter (impulse=30, min impulse=2.0%, pullback depth=50%, stabilization=5 bars, scale out=50%, stop=0.2%) was tuned.
- **Clean Scope Maintained:** Direct KRX/Tokyo execution, KXIAY, candidate 2x ETFs, and generic USD remain strictly excluded.
- **Level-2 & Options Gates:** True Level-2 book data and historical option chains remain UNVALIDATED; covered calls remain blocked from headline replication.
- **Data Period Status:** July–September 2026 remains strictly `POST_HOC_HOLDOUT / NOT_PRISTINE_OOS`. Pristine out-of-sample data remains `UNAVAILABLE`.
