# V2-F Frozen Microstructure Specification & Policy

## 1. Objective and Authority

This document defines the frozen Level-2 microstructure policy for Phase O (V2-F Ablation), per [`docs/execution_plan/REDDIT_V2_THREE_TRACK_RESEARCH_COORDINATION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_THREE_TRACK_RESEARCH_COORDINATION_PLAN.md) and [`docs/execution_plan/REDDIT_V2_V2F_LEVEL2_EXECUTION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_V2F_LEVEL2_EXECUTION_PLAN.md).

This policy is frozen **prior** to evaluating prospective out-of-sample data to ensure cross-track independence and prevent performance-driven parameter tuning.

---

## 2. Scientific Objective: Information-Set Ablation

The primary scientific objective is to determine whether genuine order-book depth and liquidity signals (as described qualitatively by the Reddit source) add predictive or decision value to the tactical entry decision when all other mechanics are held constant.

- **Control:** `V2_OHLCV_BASELINE` (frozen V2 signal sequence using 1-minute OHLCV).
- **Treatment:** `V2_LEVEL2_MICROSTRUCTURE` (identical frozen V2 sequence augmented with order-book gating).
- **Invariant:** Execution economics (slippage, commissions, timing) remain strictly identical between Control and Treatment in the primary ablation to isolate pure informational value.

---

## 3. Evidence Status

- **OBSERVED:** Reddit source mentions monitoring Level-2 depth, bid/ask walls, order book liquidity, and waiting for queue depletion/replenishment before entering.
- **ASSUMPTION / HYPOTHESIS:** Specific mathematical thresholds (depth levels, imbalance ratio, wall size multiple, persistence duration) are hypotheses and must never be labeled observed facts.

---

## 4. Frozen Microstructure Features and Gating Thresholds

| Microstructure Metric | Definition / Formulation | Frozen Threshold | Evidence Class |
|---|---|---|---|
| **Book Depth** | Top $N$ price levels reconstructed from MBO/MBP | $N = 5$ price levels | `DERIVED` |
| **Top-5 Book Imbalance** | $\frac{\text{BidDepth}_5 - \text{AskDepth}_5}{\text{BidDepth}_5 + \text{AskDepth}_5}$ | $\ge +0.20$ (buy-side dominance) | `HYPOTHESIS` |
| **Spread Constraint** | $\text{Ask}_1 - \text{Bid}_1$ | $\le 2 \times \text{MinTick}$ | `HYPOTHESIS` |
| **Bid Wall Detection** | Bid size at a single level $\ge 3 \times$ median level size | Present at or within 2 ticks of bid | `HYPOTHESIS` |
| **Depletion & Replenishment** | Bid depth increases following stabilization trough | Positive replenishment confirmed | `HYPOTHESIS` |

---

## 5. Decision Integration Semantics

Order book gating is applied strictly as an entry confirmation filter at the conclusion of the stabilization window:
$$\text{Tactical Entry} = \text{Impulse} \land \text{Pullback} \land \text{Stabilization} \land \text{Reclaim} \land \text{Level2\_Gate}$$

If `Level2\_Gate` is False, the entry attempt is vetoed/deferred. Tactical exits (stops and targets) continue to follow the frozen V2 mechanics.

---

## 6. Authentic Data Gate & Prohibitions

1. **Synthetic Level-2 Strictly Forbidden:** Cannot synthesize order books from OHLCV bars or volume tick interpolations.
2. **Point-in-Time Event Replay:** Reconstructed book state must use strictly past market-by-order (MBO) or market-by-price (MBP) events available at decision timestamp $t$. Zero lookahead.
3. **Quarantine Unsynchronized Data:** Intervals with crossed books, inverted sequence numbers, or unresolvable gaps must be reported and quarantined.
