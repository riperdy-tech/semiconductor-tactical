# Gemini Handoff — Post-First-Real-Run Audit

## Objective

Execute docs/execution_plan/POST_FIRST_REAL_RUN_AUDIT.md.

The first genuine Massive 1-minute historical run is strongly negative. Your job is to verify that the implementation and research protocol are measuring the intended experiment correctly.

Do not optimize the strategy to improve the result.

## Read first

1. AGENTS.md
2. docs/REDDIT_SOURCE_NOTES.md
3. docs/STRATEGY_SPEC.md
4. docs/BACKTEST_PROTOCOL.md
5. docs/DATA_CONTRACT.md
6. docs/DECISIONS.md
7. docs/execution_plan/FINAL_GATE_FIX.md
8. docs/execution_plan/MASSIVE_DATA_INGESTION.md
9. docs/execution_plan/POST_FIRST_REAL_RUN_AUDIT.md
10. configs/base.yaml
11. configs/historical_1m.yaml, if present
12. src/tactical_engine/backtest/engine.py
13. src/tactical_engine/signals/exits.py
14. src/tactical_engine/portfolio/sizing.py
15. src/tactical_engine/research/comparison.py

## Phase A — preserve evidence

Before modifying code:

- identify the first real-data run;
- preserve report and comparison JSON;
- record dataset ID and aggregate hash;
- record exact git SHA;
- record exact config;
- verify USD inclusion;
- verify .env/API credentials are not tracked.

Do not delete the first-run artifact.

## Phase B — correct ATR exit geometry

Inspect how ATR is used in sizing and exits.

Required design:

- compute exit geometry at entry;
- store entry ATR, initial stop, initial target, and entry timestamp;
- use stored geometry throughout the trade;
- only introduce dynamic/trailing behavior if explicitly specified.

Add regression tests for later volatility expansion and contraction.

Do not change ATR multiples to improve performance.

## Phase C — document current signal semantics

Document exactly what literal_clone, risk_controlled, and regime_adapted do:

- sector filter;
- trend confirmation;
- pullback threshold;
- relative-volume threshold;
- event filter;
- exit family;
- leverage and layering.

Do not add an unstated trend rule and call it observed Reddit behavior.

## Phase D — add diagnostics, not tuning

Add reporting for:

- trades/day;
- trades/symbol/day;
- median holding time;
- signal count versus filled entries;
- simultaneous exposure;
- re-entries;
- gross P&L;
- each cost component;
- financing;
- net P&L.

Do not tune to the observed Reddit trade count.

## Phase E — freeze OOS boundaries

Create or update the authoritative 1-minute research config with explicit:

- start;
- train_end;
- validation_end;
- test_start;
- end.

The dates must come from the research protocol/source period, not observed performance.

Store them in the config, run manifest, report, and docs/DECISIONS.md.

## Phase F — verification

Run:

.un.ps1 test

.un.ps1 doctor

.un.ps1 doctor-data -Config <1m-config> -DataDir data/processed

and:

.\.venv\Scripts\python.exe -m ruff check .

Then run the formal historical comparison only with the explicit frozen 1-minute config.

Do not tune on TEST_OOS.

## Required final response from Gemini

Report:

1. files changed;
2. tests added;
3. tests passed;
4. exact config used;
5. exact OOS boundaries;
6. first-run artifact path;
7. dataset ID and aggregate SHA;
8. whether USD was included;
9. confirmation that no strategy parameter was optimized;
10. remaining blockers.

Do not declare the strategy successful or unsuccessful based only on the full-sample result.

## Definition of done

All audit acceptance criteria pass, then stop coding.

The next step is a clean formal OOS research execution and interpretation.
