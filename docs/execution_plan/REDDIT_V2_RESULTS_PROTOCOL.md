# Reddit Behavioral Replication V2 — Results & Experiment Protocol

## 1. Experiment Matrix (V2-A through V2-F)

To decouple the economic contribution of each structural layer, research in V2 is evaluated across an incremental 6-tier ablation matrix:

```
┌────────────────────────────────────────────────────────────────────────┐
│ V2-A: Core Portfolio Only (Persistent inventory, no active trading)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ + Tactical sleeve
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ V2-B: Core + Tactical Trading (Cash-funded scalps/swings around core)  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ + Account margin financing
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ V2-C: Core + Tactical + Margin (2x max leverage, 5% financing rate)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ + Validated covered-call overlay
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ V2-D: Core + Tactical + Margin + Covered Calls (Real option chains)    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ + Composite U.S. universe
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ V2-E: Full Validated U.S.-Market Composite Execution                  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Information set ablations
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ V2-F: Information Ablations (OHLCV baseline vs true Level 2 depth)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tier Specifications & Gating Criteria

| Experiment Tier | Configuration Scope | Primary Assets Evaluated | Key Invariants & Gates | Required Status Label |
|---|---|---|---|---|
| **V2-A** | Core Portfolio Only | MU, SNDK, SKHY (U.S.) | Unlevered persistent holding (60% normalized scenario); static hold (no monthly rebalance); zero tactical trading. Baseline benchmark. | `BENCHMARK` |
| **V2-B** | Core + Tactical Trading | MU, SNDK, SKHY | Tactical add/reduce around core; cash funded; tactical exits never liquidate core. | `EVALUABLE` |
| **V2-C** | Core + Tactical + Margin | MU, SNDK, SKHY | Margin debt permitted up to 2.0x leverage; 5% annual interest; 25% maintenance margin. | `EVALUABLE` |
| **V2-D** | Core + Tactical + Margin + Covered Calls | MU, SNDK, SKHY + Options | Covered calls on owned shares; buyback on pullback. Hard gate: requires real option quotes. | `GATED_UNVALIDATED` (without real chains) |
| **V2-E** | Full Validated U.S.-Market Composite | MU, SNDK, SKHY (+ verified 2x proxies) | Integrates all validated U.S. components. Does NOT claim full Reddit replication if Asia/Level-2 unvalidated. | `PARTIAL_US_REPLICATION` |
| **V2-F** | Information Set Ablations | All eligible assets | Compares OHLCV-only rules vs validated microstructure inputs (Level 2). | `ABLATION` |

---

## 3. Epistemic Guardrails for Research Reporting

1. **Replication Declaration Rule**:
   Under no circumstances may V2-E be declared a "full replication of the Reddit trader's strategy" unless:
   - Level-2 order-book data is acquired and validated;
   - Real historical option chains are acquired and validated;
   - The unmodeled Asian execution component (KRX / Tokyo) is acknowledged.
2. **Current Global Status**:
   ```
   FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED
   DIRECT_ASIA_REPLICATION_STATUS    = OUT_OF_SCOPE_FOR_V2
   TRUE_LEVEL2_REPLICATION          = UNVALIDATED
   HISTORICAL_OPTION_CHAIN_STATUS   = UNVALIDATED
   PRISTINE_OOS_STATUS              = UNAVAILABLE
   ```
3. **No Curve-Fitting to $550k**:
   The headline target is to explain the **portfolio mechanics and risk characteristics**, not to tune parameters until the model hits $550k or ~1,300 trades.
4. **Mandatory Reporting Metrics**:
   Every V2 report must state:
   - Initial cash, ending equity, total net P&L;
   - Core realized/unrealized P&L vs tactical realized/unrealized P&L;
   - Covered-call realized P&L and delivered share P&L;
   - Total margin financing interest accrued;
   - Total commissions and slippage;
   - Maximum drawdown, Sharpe ratio, Sortino ratio, win rate, and profit factor;
   - Complete data provenance, git SHA, and parameter registration IDs.
