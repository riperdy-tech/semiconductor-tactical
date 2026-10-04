# Phase K Baseline Preservation Note

**Preserved Baseline ID:** `PHASE_K_REPORTED_RESULT`  
**Run ID:** `5080f859`  
**Commit SHA:** `1eda7cc` (parent `ae8ee91`)  
**Date Generated:** `2026-10-03T16:44:09.306981+00:00`  
**Dataset ID:** `massive_stocks_1m_51e9b529de55`  
**Dataset SHA256:** `51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8`  
**Historical Period:** `2026-07-01T00:00:00Z to 2026-09-30T23:59:59Z`  
**Evaluation Status:** `POST_HOC_HOLDOUT / NOT_PRISTINE_OOS`  

---

## 1. Preserved Phase K Performance Metrics

| Metric | V2-A: Core Only | V2-B: Core + Tactical | V2-C: Core + Tactical + Margin |
|---|---|---|---|
| **Strategy Description** | 60% Static Core | Core + Tactical (Cash) | Core + Tactical + Margin |
| **Initial Cash** | $100,000.00 | $100,000.00 | $100,000.00 |
| **Final Net Equity** | $106,482.16 | $107,384.62 | $107,384.62 |
| **Total Net P&L** | +$6,482.16 | +$7,384.62 | +$7,384.62 |
| **Total Net Return** | +6.48% | +7.38% | +7.38% |
| **Maximum Drawdown** | 20.82% | 23.43% | 23.43% |
| **Core Unrealized P&L** | +$6,482.16 | +$6,482.16 | +$6,482.16 |
| **Core Realized P&L** | $0.00 | $0.00 | $0.00 |
| **Tactical Realized P&L** | $0.00 | -$4,329.92 | -$4,329.92 |
| **Tactical Unrealized P&L** | $0.00 | +$5,232.38 | +$5,232.38 |
| **Tactical Net Contribution** | Benchmark | +$902.46 (+0.90% return spread) | +$902.46 (+0.90% return spread) |
| **Tactical Trade Count** | 0 | 123 | 123 |
| **Tactical Adds / Reloads** | 0 / 0 | 96 / 32 | 96 / 32 |
| **Tactical Partial Exits** | 0 | 33 | 33 |
| **Tactical Full Exits** | 0 | 61 | 61 |
| **Tactical Win Rate (%)** | N/A | 32.5% | 32.5% |
| **Median Holding Time** | N/A | 19.0 minutes | 19.0 minutes |
| **Peak Margin Debt** | $0.00 | $0.00 | $0.00 |
| **Margin Interest Paid** | $0.00 | $0.00 | $0.00 |
| **Slippage Paid** | $0.00 | $742.21 | $742.21 |
| **Accounting Invariant** | Clean (`True`) | Clean (`True`) | Clean (`True`) |

---

## 2. Frozen V2 Candidate Signal Parameters

- `impulse_lookback_bars`: 30 minutes
- `min_impulse_magnitude`: 0.020 (2.0%)
- `pullback_depth_fraction`: 0.500 (50%)
- `stabilization_bars`: 5 bars
- `tactical_scale_out_ratio`: 0.50 (50%)
- `tactical_stop_mode`: "LOCAL_LOW" (0.2% buffer)
- `rebound_target_ratio`: 0.50 (50%)

---

## 3. Purpose of Preservation

This note and the archived artifacts in `reports/fidelity_runs/phase_k_baseline_1eda7cc/` serve as an immutable record of the Phase K result prior to the Phase L post-run audit and accounting corrections. Phase L will produce a separate `PHASE_L_CORRECTED_RESULT` without overwriting or obscuring the historical Phase K run.
