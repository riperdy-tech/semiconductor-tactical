# V2-D Frozen Covered-Call Option Policy

## 1. Objective and Authority

This document defines the frozen covered-call writing policy for Phase N (V2-D Reconstruction), per [`docs/execution_plan/REDDIT_V2_THREE_TRACK_RESEARCH_COORDINATION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_THREE_TRACK_RESEARCH_COORDINATION_PLAN.md) and [`docs/execution_plan/REDDIT_V2_V2D_OPTIONS_EXECUTION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_V2D_OPTIONS_EXECUTION_PLAN.md).

This policy is frozen **prior** to evaluating prospective out-of-sample data to ensure cross-track independence and prevent performance-driven parameter tuning.

---

## 2. Evidence Status & Scientific Classification

- **OBSERVED:** Reddit source mentions writing short-dated covered calls against long holdings during strength, and repurchasing them during pullbacks.
- **ASSUMPTION / HYPOTHESIS:** Exact numerical parameters (DTE, target delta, sell triggers, buyback thresholds, allocation to core vs tactical shares) are hypotheses and must never be labeled observed facts.

---

## 3. Frozen Option Policy Parameters

| Parameter | Frozen Default | Permitted Sensitivity Range | Evidence Class |
|---|---|---|---|
| **Target DTE** | `5 calendar days` | 3 to 7 calendar days | `ASSUMPTION` |
| **Moneyness / Target Delta** | `0.20 OTM Delta` | 0.20 to 0.30 OTM Delta | `HYPOTHESIS` |
| **Eligible Collateral** | Long core equity shares only | Long core equity shares | `DERIVED` |
| **Covered Ratio** | 1 contract per 100 eligible shares (floor) | Max fully covered | `DERIVED` |
| **Writing Trigger** | After confirmed upward impulse (`+2.0%`) | Strength event | `HYPOTHESIS` |
| **Buyback Rule 1 (Decay)** | Option ask <= 50.0% of initial premium | 50.0% decay | `HYPOTHESIS` |
| **Buyback Rule 2 (Pullback)** | Underlying price <= -2.0% from sale reference | 2.0% pullback | `HYPOTHESIS` |
| **Execution Mechanics** | Sell at bid, buyback at ask | Executable book | `DERIVED` |
| **Assignment Handling** | Physical delivery of core shares | Standard assignment | `DERIVED` |

---

## 4. Execution Rules & Hard Invariants

1. **Covered-Share Invariant:**
   $$\text{Short Call Contracts} \times 100 \le \text{Eligible Owned Long Shares}$$
   Under no circumstances may naked or uncovered calls be written. Tactical shares are not eligible collateral for covered writing unless explicitly converted to core.
2. **Authentic Data Gate:**
   - Must use point-in-time historical bid/ask quotes from an authenticated provider.
   - Synthetic Black-Scholes fills are strictly prohibited for headline execution.
   - If no executable quote exists at decision time, record `NO_EXECUTABLE_OPTION_QUOTE` and do not fill.
3. **Execution Economics:**
   - Short call entry fills at executable **bid**.
   - Buyback fills at executable **ask**.
   - Full spread cost, exchange/clearing fees, and contract commissions must be accounted for.
4. **Attribution Separation:**
   - Option premiums, buyback costs, and assignment P&L must be segregated from underlying equity sleeve P&L.
   - Immutable control is V2-C; incremental contribution is $\text{V2-D} - \text{V2-C}$.
