# Post-Audit Research Integrity Execution Package

**Date:** 2026-10-02  
**Repository:** `riperdy-tech/semiconductor-tactical`

This package is the next implementation pass after `INSTRUCTIONS.md` and commit `99f4f38`.

## Objective

Close the four remaining research-integrity gaps before genuine market data is introduced:

1. enforce the `REAL_HISTORICAL_VERIFIED` gate;
2. implement true train/validation/test OOS evaluation for all three strategy variants;
3. distinguish benchmark-return bootstrap diagnostics from strategy-level robustness analysis;
4. run the final falsification suite against the actual OOS experiment, not merely the full sample.

The package deliberately does **not** acquire market data, fabricate data, optimize parameters, or attempt to reproduce the Reddit headline result.

## Execution order

| Step | Deliverable | Gate |
|---|---|---|
| 1 | Dataset verification gate | Unverified/synthetic data cannot enter a research-evidence path |
| 2 | OOS experiment architecture | Train/validation/test exists for all 3 variants |
| 3 | Strategy-level robustness | Falsification operates on strategy results, with methodology labels |
| 4 | Final research report | IS/validation/OOS + robustness are reported together |
| 5 | CI + CLI verification | One-command workflow and tests are green |
| 6 | Research handoff | Repo is ready to receive genuine market data |

## Source of truth

Follow, in order:

1. `AGENTS.md`
2. `INSTRUCTIONS.md`
3. `docs/STRATEGY_SPEC.md`
4. `docs/BACKTEST_PROTOCOL.md`
5. `docs/DATA_CONTRACT.md`
6. `docs/IMPLEMENTATION_PLAN.md`
7. `docs/AUDIT_20261002_POST_GEMINI.md`
8. this execution package

## Completion rule

This package is complete only when all acceptance criteria in `ACCEPTANCE_TESTS.md` pass.

Even after completion:

**ENGINE IMPLEMENTATION:** substantially complete  
**HISTORICAL STRATEGY RESEARCH:** not complete until genuine verified market data is supplied and the final OOS run is executed  
**OPTIONS RESEARCH:** unvalidated  
**EVENT FILTERING:** partial / unvalidated
