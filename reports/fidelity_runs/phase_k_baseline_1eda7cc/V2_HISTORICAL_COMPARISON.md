# Reddit Behavioral Replication V2 — Historical Comparison Report

**Run ID:** `5080f859`  
**Date Generated:** `2026-10-03T16:44:09.306981+00:00`  
**Git Commit SHA:** `ae8ee91`  
**Dataset ID:** `massive_stocks_1m_51e9b529de55`  
**Dataset SHA256:** `51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8`  
**Historical Period:** `2026-07-01T00:00:00Z to 2026-09-30T23:59:59Z`  
**Evaluation Status:** `POST_HOC_HOLDOUT / NOT_PRISTINE_OOS`  

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
> **Scope Boundaries & Assumptions:**
> 1. **U.S.-Market Only Scope:** Direct execution on KRX and Tokyo is out of scope.
> 2. **Clean Universe:** Evaluated strictly on `MU`, `SNDK`, and `SKHY`.
> 3. **Excluded Proxies:** Generic `USD` ETF, candidate 2x ETFs, and `KXIAY` OTC ADR.
> 4. **Core Assumption:** The 60% normalized core allocation is a research assumption chosen because the source describes persistent large holdings but does not disclose exact starting weights.
> 5. **No Parameter Tuning:** Pre-registered parameters frozen before evaluation.

---

## 2. Comparative Performance Matrix (V2-A, V2-B, V2-C)
| Performance & Risk Metric | V2-A: Core Only | V2-B: Core + Tactical | V2-C: Core + Tactical + Margin |
|---|---|---|---|
| **Strategy Description** | 60% Static Core | Core + Tactical (Cash) | Core + Tactical + Margin |
| **Initial Cash** | $100,000.00 | $100,000.00 | $100,000.00 |
| **Final Net Equity** | $106,482.16 | $107,384.62 | $107,384.62 |
| **Total Net P&L** | $6,482.16 | $7,384.62 | $7,384.62 |
| **Total Return (%)** | **+6.48%** | **+7.38%** | **+7.38%** |
| **Maximum Drawdown (%)** | 20.82% | 23.43% | 23.43% |
| **Core Unrealized P&L** | $6,482.16 | $6,482.16 | $6,482.16 |
| **Core Realized P&L** | $0.00 | $0.00 | $0.00 |
| **Tactical Realized P&L** | $0.00 | $-4,329.92 | $-4,329.92 |
| **Tactical Trade Count** | 0 | 123 | 123 |
| **Tactical Adds / Reloads** | 0 / 0 | 96 / 32 | 96 / 32 |
| **Tactical Partial Exits** | 0 | 33 | 33 |
| **Tactical Full Exits** | 0 | 61 | 61 |
| **Tactical Win Rate (%)** | N/A | 32.5% | 32.5% |
| **Median Holding Time** | N/A | 19.0m | 19.0m |
| **Peak Margin Debt** | $0.00 | $0.00 | $0.00 |
| **Margin Interest Paid** | $0.00 | $0.00 | $0.00 |
| **Margin Calls / Liquidations** | 0 / 0 | 0 / 0 | 0 / 0 |
| **Commissions Paid** | $0.00 | $0.00 | $0.00 |
| **Slippage Paid** | $0.00 | $742.21 | $742.21 |
| **Accounting Invariant** | Clean (`True`) | Clean (`True`) | Clean (`True`) |

---

## 3. Component Attribution Analysis

### Key Findings:
1. **Tactical Contribution (V2-B vs V2-A):** $+902.47 (+0.90% return spread).
2. **Margin Impact (V2-C vs V2-B):** $+0.00 (+0.00% return spread; margin interest $0.00).
3. **Core Isolation Integrity:** Persistent core inventory remained intact.
4. **Holding Duration:** 123 trades with median hold of 19.0 min.
