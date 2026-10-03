# Reddit Strategy Fidelity Results Protocol

This protocol defines the execution, logging, and evaluation procedures for the **Reddit Strategy Fidelity Experiments** per `docs/execution_plan/REDDIT_STRATEGY_FIDELITY_EXECUTION_PLAN.md`.

---

## 1. Protocol Objectives

1. Preserve the original negative result (`CURRENT_MECHANICAL_PULLBACK_BASELINE`) as an immutable empirical benchmark.
2. Formally decouple the directional equity strategy from options overlays, leverage/margin, and extended-hours trading.
3. Enforce the data sufficiency gate: refuse to declare covered calls or non-RTH trading as "validated" without authentic primary market data.
4. Prevent retroactive parameter tuning against the $550k claim, the 1,300 trade count, or the historical sample.

---

## 2. Core Experiment Matrix Definitions

### Experiment 1: Preserved Baseline (`CURRENT_MECHANICAL_PULLBACK_BASELINE`)
- **Variant:** `current_mechanical_pullback_baseline` (Run `2e9f108d`, config hash `0d34835d97140803`)
- **Signal:** 1-minute rolling 60-bar z-score $\le -1.5$, relative volume $\ge 0.70$, sector filter `False`.
- **Exit:** 1.0x entry ATR target, 1.0x entry ATR stop, 120-minute maximum hold.
- **Leverage:** 1.0x gross leverage, max 1 layer, 25% max symbol weight.
- **Costs:** 0.0 bps commission, 5.0 bps slippage, 5.0% margin interest.
- **Order Model:** Next-bar market orders.
- **Options:** Disabled.
- **Execution Role:** Immutable preserved historical baseline establishing the cost-drag and rapid-stop mechanics of high-frequency mean-reversion (-92.89% return, 5,082 trades).

### Diagnostic: Sector-Filtered Mechanical Pullback (`MECHANICAL_PULLBACK_SECTOR_FILTERED_DIAGNOSTIC`)
- **Variant:** `mechanical_pullback_sector_filtered_diagnostic`
- **Signal:** Same mechanical pullback, with sector filter `True`.
- **Execution Role:** Evaluates the isolated impact of sector filtering on the mechanical baseline (~ -34.88% / -35.69% return, ~1,114 / 1,129 trades). Strictly a diagnostic; never substituted for the baseline.

### Experiment 2: Directional Fidelity (`DIRECTIONAL_FIDELITY_RECONSTRUCTION`)
- **Variant:** `directional_fidelity_reconstruction`
- **Signal:** Directional swing pullback proxy:
  - Intraday trend intact (`trend_slope > 0`, MA alignment, optional SMH sector confirmation).
  - Dip from recent high between 0.5% and 3.0% (`-0.030 <= dist_high <= -0.005`).
  - Bar stabilization (close in upper 35% of bar or positive return).
- **Exit:** Multi-bar swing targets (2.5x ATR target, 1.5x ATR stop, 240m max hold).
- **Order Model:** Stop-limit orders with ceiling limit price to prevent adverse fill slippage [HYPOTHESIS entry proxy].
- **Leverage:** 1.0x unleveraged cash account (isolating directional signal edge).
- **Options:** Disabled.
- **Parameter Provenance:** `POST_HOC_SPECIFIED` per `docs/execution_plan/REDDIT_FIDELITY_PARAMETER_PROVENANCE.md`.
- **Execution Role:** Evaluates whether directional semiconductor swing trading can generate positive expectancy independent of options or leverage (-53.27% return, 1,334 trades).

### Experiment 3: Directional + Margin (`DIRECTIONAL_FIDELITY_MARGIN`)
- **Variant:** `directional_fidelity_reconstruction` with margin.
- **Leverage:** 1.5x gross leverage, max 2 layers.
- **Financing:** 5.0% annual borrowing rate, margin debt tracking, maintenance requirement monitoring, forced liquidation simulation.
- **Options:** Disabled.
- **Execution Role:** Quantifies whether reported performance characteristics could arise from leverage amplification vs underlying signal edge (-58.51% return, 1,369 trades).

### Experiment 4: Directional + Covered Calls (`COVERED_CALL_OVERLAY`)
- **Status:** `UNVALIDATED` (Gated by data sufficiency).
- **Rule:** Write short-dated OTM covered calls when underlying reaches strength (`check_strength_predicate`); repurchase on pullbacks.
- **Protocol Constraint:** Without verified historical option-chain tick data, option cash flows must not be merged into headline equity results.

### Experiment 5: Full Validated Composite (`FULL_VALIDATED_COMPOSITE`)
- **Status:** `BLOCKED_BY_DATA_GATE`.
- **Constraint:** Requires simultaneous validation of RTH equity, extended hours, option chains, and margin.

### Experiment 6: Component Ablations
- Evaluates individual mechanics:
  - `mechanical_pullback_sector_filtered_diagnostic`
  - `equity_only_1.0x` vs `equity_plus_margin_1.5x` vs `equity_plus_margin_2.0x`
  - `market_orders` vs `stop_limit` orders
  - `sector_filter_on` vs `sector_filter_off`

---

## 3. Epistemic Labeling Rules

Every parameter and rule in reports and code must carry an epistemic label:
- `OBSERVED`: Explicitly described in the Reddit post/comments.
- `DERIVED`: Necessary mechanical inference from observed facts.
- `HYPOTHESIS`: Deterministic proxy chosen to approximate discretionary chart reading.
- `ASSUMPTION`: Parameter chosen because the source is silent.
- `UNVERIFIED`: Information that cannot currently be checked with primary data.

---

## 4. Descriptive Plausibility Protocol

Before assessing profitability, report:
- `trades_per_day`
- `trades_per_symbol_per_day`
- `median_holding_time_minutes`
- `max_simultaneous_positions`
- `reentry_count`
- `time_in_market_pct`
- `costs_as_pct_of_gross_pnl`

These metrics are compared against the source's descriptive claims (~1,300 trades, multi-hour/multi-day swing positions) **strictly as descriptive reality checks**. They must never be used as optimization targets.
- **Trade Count Note:** The similarity between 1,334 trades and the source's ~1,300 claim is not treated as validation of the strategy.
- **Holding Time Note:** The 8.0-minute median hold time represents reduced high-frequency churn relative to the 2.0-minute baseline, but does not prove that the Reddit trader held positions for similar durations.

---

## 5. P&L Accounting and Reconciliation Invariant

The simulation engine maintains mathematical reconciliation across all P&L and cost components:
```
Signal-Price P&L (Pre-Slippage)
  - Execution Slippage (embedded directly into fill prices)
  = Gross Realized Trading P&L
  - Commission Paid
  = Net Realized Trading P&L
  + Options Realized P&L
  - Margin Interest Paid
  = Portfolio Net P&L
  = Final Equity - Initial Cash (for closed positions)
```
**No Double-Counting Rule:** Execution slippage is reflected directly in entry and exit fill prices; it is never subtracted a second time from Net Realized P&L.

---

## 6. Stop Condition

Once the fidelity matrix runs, produces canonical JSON and Markdown outputs, passes tests, and satisfies all acceptance criteria:
**STOP SOFTWARE CHANGES.**
Do not iterate to seek positive returns. The research status remains:
- `FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED`
- `PRISTINE_OOS = UNAVAILABLE`

