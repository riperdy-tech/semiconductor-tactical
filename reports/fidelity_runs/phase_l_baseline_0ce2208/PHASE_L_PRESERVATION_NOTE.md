# Phase L Preservation Note

- **Preservation Date:** 2026-10-04T18:23:45Z
- **Preserved Git Commit SHA:** `0ce2208`
- **Status Classification:** `PHASE_L_REPORTED_RESULT`
- **Context:**
  This directory preserves the canonical Phase L post-run audit artifacts (`reports/V2_HISTORICAL_COMPARISON.md` and `reports/v2_historical_comparison.json`) prior to the Phase L.1 accounting reconciliation and reproducibility fix.
  
  The prior Phase K baseline is preserved at `reports/fidelity_runs/phase_k_baseline_1eda7cc/` under `PHASE_K_REPORTED_RESULT`.
  The forthcoming corrected result from Phase L.1 will be labeled `PHASE_L1_CORRECTED_RESULT`.

## Preserved Metrics (Phase L Reported Result)
- **V2-A (Core Only) Return:** +6.48% ($106,482.16 ending equity)
- **V2-B (Core + Tactical Cash) Return:** +7.93% ($107,928.85 ending equity)
- **V2-C (Core + Tactical + Margin) Return:** +7.93% ($107,928.85 ending equity)
- **Tactical Realized P&L Reported:** +$1,446.69
- **Reported Slippage Total:** $1,563.81
- **Effective Start Window:** 2026-07-13T13:30:00Z to 2026-09-30T19:59:00Z
- **Pre-Correction Accounting Issue Flagged:**
  In Phase L, total reported execution slippage ($1,563.81) may include entry slippage on terminal open tactical positions, while closed reference P&L ($3,010.50) only reflects completed FIFO round trips. Phase L.1 reconciles the closed vs. open slippage attribution and proves all accounting invariants algebraically without altering any strategy parameters.
