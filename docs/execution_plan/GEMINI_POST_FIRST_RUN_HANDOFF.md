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

.\run.ps1 test

.\run.ps1 doctor

.\run.ps1 doctor-data -Config <1m-config> -DataDir data/processed

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

## Phase G — OOS and provenance reconciliation

Before any formal research interpretation, execute:

docs/execution_plan/OOS_PROVENANCE_RECONCILIATION.md

This phase is mandatory because the first full-period run exposed the later September partition before the OOS boundaries were frozen, and the post-audit report currently contains configuration and aggregate-hash claims that must be reconciled against the actual run artifacts and checked-in manifest.

Do not call September a pristine OOS result unless the evidence proves it was previously unseen. Do not silently regenerate the historical run to make the provenance agree.

After reconciliation, stop software changes unless a real defect is found.

## Phase H — Reddit strategy fidelity reconstruction

Before further strategy performance interpretation, execute:

docs/execution_plan/REDDIT_STRATEGY_FIDELITY_EXECUTION_PLAN.md

This phase is mandatory because the existing backtest engine is operationally complete but the current strategy implementation is not a faithful reconstruction of the full behavior described by the source.

The current negative result must remain preserved as:

CURRENT_MECHANICAL_PULLBACK_BASELINE

Do not discard it, overwrite it, or relabel it as the Reddit trader's actual strategy.

The fidelity task must:

- build a source-evidence matrix using OBSERVED / DERIVED / HYPOTHESIS / ASSUMPTION / UNVERIFIED labels;
- identify the gap between the current z-score/ATR mean-reversion implementation and the source's described directional trading behavior;
- model directional equity trading separately from covered calls, margin/capital deployment, and extended-hours activity;
- require real historical option-chain data before covered-call P&L is treated as validated;
- explicitly classify unsupported extended-hours behavior as UNVALIDATED when data is unavailable;
- preserve no-lookahead, execution, provenance, and OOS controls;
- compare descriptive trading behavior without fitting parameters to the reported $550k result or reported trade count.

Do not optimize for profitability, trade-count matching, or resemblance to the reported account equity.

Stop after the fidelity acceptance criteria pass.

## Phase I — Phase H post-run research integrity correction

Before any further strategy experiment, execute:

docs/execution_plan/GEMINI_PHASE_H_POST_RUN_CORRECTION.md

This phase is mandatory. It is a research-bookkeeping correction only.

Do not modify the frozen directional strategy parameters.

The correction must:

- restore the exact preserved CURRENT_MECHANICAL_PULLBACK_BASELINE identity;
- separate that baseline from later sector-filtered mechanical diagnostics;
- establish parameter provenance from git history;
- classify key directional parameters as PRE_SPECIFIED, POST_HOC_SPECIFIED, or UNKNOWN;
- correct P&L/slippage/commission/financing terminology and verify no double counting;
- classify stop-limit entry as a HYPOTHESIS rather than an observed source rule;
- avoid describing 8-minute median holding time as validated swing behavior;
- preserve all historical artifacts;
- add regression tests for these research-integrity rules.

Do not rerun the strategy to search for better parameters.

After Phase I passes, stop software changes again.

The research status must continue to state:

FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED

and:

PRISTINE_OOS = UNAVAILABLE

## Phase J — Reddit Behavioral Replication V2 (US-market scope)

After Phase I passes, execute:

docs/execution_plan/REDDIT_BEHAVIORAL_V2_EXECUTION_PLAN.md

This is the next substantive reconstruction phase.

V2 must model the Reddit source as a portfolio process rather than a single buy/sell signal, including:

- persistent core holdings;
- tactical add/reduce/re-entry around those holdings;
- account-level margin;
- covered calls attached to owned shares;
- stop-limit execution;
- Level-2 as a separate data gate;
- U.S.-market-only execution.

### V2 instrument scope

Use:

- MU;
- SNDK;
- SKHY;
- U.S.-market KXIAY only when historical data is sufficient and clearly labeled as a U.S. ADR proxy;
- verified U.S.-listed 2x products only after source-evidence and data validation.

Do not model direct:

- KRX 000660;
- Tokyo 285A.

Set:

DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2

Do not include the current generic USD semiconductor ETF in the source-replication headline unless primary-source evidence establishes that it represents the trader's actual 2x exposure.

### V2 fidelity rules

The V2 plan requires:

- a new source evidence matrix;
- explicit separation of source-identified ETFs from candidate proxy ETFs;
- persistent holdings separate from tactical positions;
- covered calls linked to owned shares;
- genuine Level-2 data gated as UNVALIDATED when absent;
- U.S.-only session scope;
- pre-registered V2 parameters;
- no July–September parameter selection;
- no optimization toward $550k, ~1,300 trades, or profitability.

Do not reuse the Phase H post-hoc directional parameter set as if it were pre-registered V2.

After the V2 specification, instrument manifest, parameter registry, data gates, tests, and documentation pass:

STOP SOFTWARE CHANGES.

The next action requires a separately approved V2 research execution.

The research status must remain:

FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED

and:

PRISTINE_OOS = UNAVAILABLE
