# V2 Frozen Prospective Out-of-Sample (OOS) Specification

## 1. Document Purpose and Authority

This specification governs Phase M: Frozen Prospective Out-of-Sample (OOS) validation of the Reddit Behavioral V2 strategy.

Per [`docs/execution_plan/REDDIT_V2_THREE_TRACK_RESEARCH_COORDINATION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_THREE_TRACK_RESEARCH_COORDINATION_PLAN.md) and [`docs/execution_plan/REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md), this document is frozen prior to exposing, ingesting, or evaluating any market data dated after 2026-09-30.

Under no circumstances may any parameter or rule in this specification be adjusted in response to prospective OOS returns or performance metrics.

---

## 2. Immutable Strategy Parameters (Frozen V2 Baseline)

The configuration parameters below match the accepted historical baseline run (Run ID `24a9e783`, Execution Code SHA `c10f91c`) exactly.

### A. Universe Definition
- **Eligible Symbols:** `MU`, `SNDK`, `SKHY`
- **Excluded Symbols / Proxies:** `USD`, `AMD`, `SMH`, `SPY`, candidate leveraged ETFs (`SKUU`, `SKHU`, `SKHL`, `MUU`, etc.), `KXIAY` ADR.
- **Market Scope:** U.S. Regular Trading Hours (RTH, 09:30–16:00 ET / 13:30–20:00 UTC).
- **Direct Asian Exchanges:** Strictly out of scope (KRX 000660 and Tokyo 6736 excluded).

### B. Core Portfolio Sleeve
- **Initial Account Capital:** $100,000.00
- **Target Core Allocation:** 60.0% of initial account capital ($60,000.00 target notional)
- **Weighting:** Equal-notional across eligible symbols (~$20,000 per symbol)
- **Sizing:** Integer share floor (`floor(target_notional / open_price)`) at the effective start timestamp
- **Rebalancing:** Static core holding; no periodic or monthly core rebalancing
- **Core Isolation:** Core shares are permanently segregated from tactical entries, tactical exits, and tactical reloads.

### C. Tactical Sleeve
- **Impulse Lookback:** 30 bars (1-minute resolution)
- **Impulse Threshold:** +2.0% minimum move (`(high - low) / low >= 0.020`)
- **Pullback Retracement Depth:** 0.500 (50% Fibonacci retracement from impulse peak to trough)
- **Stabilization Requirement:** 5 consecutive bars without breaching local pullback low
- **Entry Order:** Next-bar open market order following signal confirmation
- **Initial Stop Loss:** `LOCAL_LOW` (lowest price during stabilization window) with 0.10% buffer
- **Profit Target:** Previous impulse high (`impulse_peak`)
- **Tactical Scale-Out:** 50% position reduction upon reaching initial target
- **Trailing Stop / Remainder:** Breakeven stop on remaining 50% position
- **Maximum Layers / Re-entries:** 2 tactical layers maximum

### D. Margin & Capital Constraints (V2-C)
- **Gross Leverage Ceiling:** 2.0x of account equity
- **Maintenance Margin Ratio:** 25.0%
- **Annual Margin Financing Rate:** 5.00% (accrued per minute during debt periods)
- **Liquidation Sequence:** Tactical-first FIFO liquidation if margin call threshold is breached; core holdings liquidated only if tactical sleeve is fully depleted.

### E. Transaction Cost & Execution Model
- **Equity Commissions:** 0.0 bps ($0.00 per share)
- **Equity Slippage:** 5.0 bps (0.05% against fill price: added to buys, subtracted from sells)
- **Market Impact:** 10.0 bps per 1% bar volume participation
- **Fill Timing:** Strictly next-bar open (`bar[t+1].open`); zero lookahead fill at `bar[t].close`.

---

## 3. Strict Chronology & Sample Gate

1. **Chronological Gate:**
   - Every evaluated OOS bar must have a timestamp strictly greater than `2026-09-30T23:59:59Z`.
   - Zero bars from July 1, 2026 through September 30, 2026 may be included in OOS calculations.
2. **Sample Completeness Threshold:**
   - Minimum required sample: >= 20 complete U.S. regular trading sessions (days with >= 300 minutes of RTH data across all 3 symbols).
   - If >= 20 complete sessions exist: classify as `PHASE_M_PRISTINE_OOS_RESULT`.
   - If < 20 complete sessions exist: classify as `PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE`. No conclusive performance claim may be asserted.

---

## 4. Pre-Registered Scientific Interpretation Classes

| Classification | Scientific Condition | Research Implication |
|---|---|---|
| **SUPPORTIVE** | Tactical net contribution > 0 AND tactical win rate > 40% AND behaviorally consistent | Provides initial evidence of directional edge on unseen data |
| **NEUTRAL** | Sample size insufficient (<20 sessions) OR marginal P&L within cost noise | Inconclusive; requires longer prospective monitoring |
| **CONTRADICTORY** | Tactical net contribution < 0 OR severe degradation relative to core | Contradicts the directional tactical alpha hypothesis |
| **INVALID** | Chronology, provenance, no-lookahead, or data validation gate fails | Execution defect; result discarded from scientific record |

---

## 5. Epistemic Freeze Invariants

Even upon a successful `SUPPORTIVE` prospective OOS result, the global research status remains:

```text
FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED
TRUE_LEVEL2_REPLICATION          = UNVALIDATED (pending Phase O)
HISTORICAL_OPTION_CHAIN_STATUS   = UNVALIDATED (pending Phase N)
DIRECT_ASIA_REPLICATION_STATUS    = OUT_OF_SCOPE_FOR_V2
PRISTINE_OOS                     = VALIDATED (only for the evaluated prospective window)
```
