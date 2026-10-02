# Gemini Handoff — Execute This Package

Implement `docs/execution_plan/PLAN.md` exactly.

## What this pass is for

This is a **research-integrity correction pass**, not a strategy optimization pass.

The current repository is substantially engineered, but four issues remain:

1. unverified datasets can still enter the historical research path;
2. OOS is not yet a full train/validation/test experiment for all three variants;
3. benchmark-return bootstrap is being conflated with strategy robustness;
4. falsification is not fully tied to the final untouched OOS experiment.

## Required work

Complete the phases in this order:

1. enforce `REAL_HISTORICAL_VERIFIED` as the only research-evidence dataset status;
2. make historical CLI commands refuse synthetic and unverified data instead of warning and continuing;
3. remove the historical-command fallback to `data/sample_historical`;
4. implement explicit train/validation/test splits using the existing research dates;
5. report train/validation/test metrics separately for all 3 strategy variants;
6. label the existing stationary bootstrap as a benchmark-return diagnostic;
7. add a distinct strategy-level robustness diagnostic with explicit resampling unit;
8. connect falsification diagnostics to the final test/OOS period;
9. keep strongest-day exclusion explicitly classified as an attribution diagnostic unless it is implemented as a true rerun;
10. reconcile code, README, implementation plan, and decisions;
11. add deterministic tests for every new rule;
12. run pytest, ruff, and the canonical PowerShell commands;
13. do not acquire market data or optimize parameters.

## Hard stop conditions

Stop implementation and document the blocker if:

- genuine historical data is needed to test a research conclusion;
- an exact source-specific assumption is unavailable;
- a strategy-rule change would be required;
- an option-chain source is required.

Do not fill such gaps with fabricated data.

## Completion report

At the end, report:

- exact files changed;
- test count;
- ruff result;
- CI result;
- which CLI commands pass/fail by design;
- remaining blockers.

Do not claim historical strategy research is complete.
