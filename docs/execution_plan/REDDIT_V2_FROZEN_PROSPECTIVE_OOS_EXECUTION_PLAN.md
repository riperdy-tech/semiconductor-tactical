# Gemini Execution Plan — V2 Frozen Prospective OOS Validation

## 0. Objective and priority

Priority: P0 — first substantive research-analysis track.

Research question:

Does the already-frozen Reddit Behavioral V2 directional/core/margin hypothesis generalize to genuinely unseen chronological U.S.-market data after 2026-09-30?

This is a prospective validation experiment, not a strategy-development phase.

The July–September 2026 result remains POST_HOC_HOLDOUT / NOT_PRISTINE_OOS and must never be used to select parameters.

Accepted historical control:
- Run ID: 24a9e783
- V2-A: +6.48%, ending equity $106,482.16
- V2-B: +7.93%, ending equity $107,928.85
- V2-C: +7.93%, ending equity $107,928.85
- Tactical contribution: +$1,446.69
- Historical V2-C peak margin debt: $0.00

Do not modify those results.

## 1. Hard research-integrity rules

Forbidden:
- parameter optimization on new OOS data;
- changing impulse lookback after seeing OOS results;
- changing pullback depth after seeing OOS results;
- changing stabilization bars after seeing OOS results;
- changing scale-out after seeing OOS results;
- changing stop buffer after seeing OOS results;
- changing the 60% core allocation;
- changing MU/SNDK/SKHY;
- adding candidate leveraged ETFs, KXIAY, or USD;
- changing execution costs because of OOS performance;
- changing margin assumptions because of OOS performance;
- using OOS P&L to select a different configuration;
- grid-searching any OOS parameter;
- calling a positive OOS result "validated" if the data was exposed before the configuration was frozen.

Allowed after OOS data exposure:
- data-quality corrections;
- deterministic provenance corrections;
- mechanical bug fixes that are demonstrably independent of strategy economics.

Any allowed correction requires preserving the affected run and creating a new run ID.

## 2. Read first

Read:
1. AGENTS.md
2. docs/REDDIT_SOURCE_NOTES.md
3. docs/REDDIT_BEHAVIORAL_V2_EVIDENCE_MATRIX.md
4. docs/REDDIT_V2_DIRECTIONAL_BEHAVIOR.md
5. docs/execution_plan/REDDIT_V2_PARAMETER_REGISTRY.md
6. docs/execution_plan/REDDIT_V2_RESULTS_PROTOCOL.md
7. docs/execution_plan/REDDIT_V2_HISTORICAL_RUN_PROTOCOL.md
8. configs/historical_1m.yaml
9. src/tactical_engine/backtest/v2_engine.py
10. src/tactical_engine/signals/v2_signals.py
11. src/tactical_engine/portfolio/v2_portfolio.py
12. src/tactical_engine/execution/simulator.py
13. src/tactical_engine/research/v2_historical_runner.py
14. reports/V2_HISTORICAL_COMPARISON.md
15. reports/v2_historical_comparison.json
16. the authoritative Massive dataset manifest.

Also inspect git history to verify that only provenance/test changes occurred after c10f91c.

## 3. Freeze the strategy definition

Create:
docs/research/v2_oos/V2_OOS_FROZEN_SPEC.md

Copy the exact settings used in accepted V2 historical research.

Frozen minimum:

Universe:
- MU
- SNDK
- SKHY

Core:
- normalized initial equity: $100,000
- 60% core
- equal-notional core across the three names
- static core
- no monthly rebalance

Tactical:
- impulse lookback: 30 minutes/bars
- impulse magnitude: 2.0%
- pullback depth: 0.500
- stabilization: 5 bars
- tactical scale-out: 50%
- stop mode: LOCAL_LOW
- exact existing stop buffer
- exact existing rebound target
- exact existing signal semantics

Margin:
- exact accepted V2-C maximum leverage;
- exact maintenance model;
- exact annual margin rate;
- exact tactical-first liquidation semantics.

Costs:
- exact cost configuration used by Run 24a9e783;
- exact commission/slippage fields;
- exact config hash.

Never substitute configs/base.yaml merely for convenience.

## 4. OOS data manifest and chronology gate

Create:
reports/data_manifests/v2_oos_<id>_manifest.json

The manifest must include:
- source;
- product;
- dataset ID;
- symbol list;
- resolution;
- timezone;
- adjustment policy;
- first OOS timestamp;
- final OOS timestamp;
- row counts;
- missing-bar diagnostics;
- per-symbol SHA256;
- aggregate SHA256;
- retrieval timestamp;
- validation commit SHA.

Chronological rule:
- first eligible OOS bar must be strictly after 2026-09-30T23:59:59Z;
- no July–September bar may enter OOS return calculations;
- no backfill into the OOS period.

Minimum sample:
- require at least 20 complete U.S. regular-trading sessions after 2026-09-30;
- if fewer than 20 complete sessions exist, classify the result as PRISTINE_OOS_AVAILABLE_BUT_INSUFFICIENT_SAMPLE and do not make a performance conclusion.

Data quality:
- all three headline symbols must have valid synchronized data;
- no forward fill;
- no selective removal of adverse periods;
- any excluded row/bar must be reported.

## 5. Blindness protocol

Before inspecting OOS performance output, create and commit a freeze artifact containing:
- frozen strategy spec;
- OOS config;
- parameter fingerprint;
- OOS date policy;
- data manifest schema;
- deterministic report code;
- tests for configuration immutability.

After this commit:
- do not alter any strategy parameter;
- do not edit signal logic;
- do not change costs;
- do not change universe.

Data validation may inspect metadata, coverage, gaps, and hashes. It may not be used to cherry-pick favorable market periods.

## 6. Separate OOS runner

Do not silently modify fidelity-v2-historical.

Create a dedicated OOS entry point such as fidelity-v2-oos and a dedicated config such as configs/v2_oos_frozen.yaml.

The runner must:
1. load only the OOS dataset;
2. require REAL_HISTORICAL_VERIFIED;
3. reject any timestamp on or before 2026-09-30;
4. verify the frozen parameter fingerprint;
5. verify the frozen universe;
6. verify cost and margin hashes;
7. execute V2-A/B/C;
8. write JSON + Markdown;
9. persist all provenance;
10. label the run according to the OOS gate.

Do not refactor accepted strategy logic merely to support the runner.

## 7. Pre-run assertions

Before execution assert:
- parameter registry equals frozen V2;
- universe equals MU/SNDK/SKHY;
- cost config matches accepted historical config;
- margin config matches accepted historical config;
- no Phase H parameter appears;
- effective OOS start is strictly future of the historical sample;
- dataset is verified;
- no accepted historical artifact is being overwritten.

If any assertion fails, STOP.

## 8. Execute V2-A/B/C once

V2-A:
- persistent core only.

V2-B:
- same core plus tactical sleeve.

V2-C:
- same core and tactical behavior plus the existing margin mechanism.

Do not add a new strategy variant.

Do not perform candidate selection.

Do not rerun to improve the observed OOS result.

## 9. Required metrics

Report:

Performance:
- start equity;
- end equity;
- net return;
- daily return series;
- maximum drawdown;
- volatility;
- Sharpe;
- Sortino;
- profit factor.

Core:
- start value;
- ending value;
- realized/unrealized P&L.

Tactical:
- closed P&L;
- terminal open P&L;
- total tactical contribution;
- trade count;
- win rate;
- expectancy;
- median/percentile holding times;
- entries/reloads/partial exits/full exits;
- open inventory.

Margin:
- peak debt;
- financing;
- margin calls;
- liquidations.

Behavior:
- trades/day;
- trades/symbol/day;
- simultaneous exposure;
- turnover;
- gross exposure;
- average position size.

These are observations, not optimization targets.

## 10. Primary scientific comparisons

A. Tactical value-add:
V2-B minus V2-A.

Question:
Did tactical trading add or subtract value relative to holding the same core?

B. Margin value-add:
V2-C minus V2-B.

Question:
Did margin actually matter in the unseen period?

C. Behavioral stability:
Compare OOS versus the accepted historical run for:
- trade frequency;
- holding time;
- tactical contribution;
- drawdown;
- exposure;
- symbol concentration.

Do not optimize for similarity.

## 11. Pre-registered interpretation classes

SUPPORTIVE:
- frozen V2 produces economically positive OOS evidence and remains behaviorally plausible.

NEUTRAL / INCONCLUSIVE:
- sample too short, noisy, or ambiguous to support a conclusion.

CONTRADICTORY:
- unseen data materially contradicts the tactical hypothesis, such as a clearly negative tactical contribution or severe behavioral degradation.

INVALID:
- provenance, data-quality, no-lookahead, or configuration gate fails.

A single OOS period does not prove the Reddit trader's true strategy.

## 12. Post-run diagnostics

Only after the primary result is preserved:
- bootstrap confidence intervals on daily strategy returns;
- bootstrap confidence intervals on tactical contribution;
- benchmark-relative attribution;
- first-half versus second-half OOS;
- symbol attribution;
- concentration;
- worst-day contribution;
- trade clustering around session transitions.

These diagnostics must never be used to choose a new strategy.

## 13. Regression tests

Add tests for:
1. OOS rejects timestamps at or before 2026-09-30;
2. OOS rejects non-headline symbols;
3. OOS rejects missing common bars;
4. OOS rejects altered parameter fingerprint;
5. OOS uses frozen cost config;
6. OOS preserves no-lookahead execution;
7. OOS JSON contains dataset/config/provenance hashes;
8. OOS requires verified data;
9. V2-A/B/C share identical core initialization;
10. OOS execution cannot overwrite the accepted historical artifact.

## 14. Verification commands

Run:
- .\run.ps1 test
- .\run.ps1 doctor
- .\run.ps1 doctor-data -Config configs/v2_oos_frozen.yaml -DataDir data/processed_oos
- .\.venv\Scripts\python.exe -m ruff check .

Then execute the frozen OOS command exactly once.

Do not rerun because the result is disappointing.

## 15. Required artifacts

Create:
- docs/research/v2_oos/V2_OOS_FROZEN_SPEC.md
- configs/v2_oos_frozen.yaml
- reports/data_manifests/v2_oos_<id>_manifest.json
- reports/v2_oos/<run_id>.json
- reports/v2_oos/<run_id>.md
- reports/fidelity_runs/v2_oos_<run_id>/PRESERVATION_NOTE.md

Preservation classification:
- PHASE_M_PRISTINE_OOS_RESULT
or
- PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE

## 16. Stop conditions

STOP immediately if:
- OOS starts before 2026-10-01;
- strategy parameters change after exposure;
- Phase H parameters appear;
- result-based tuning occurs;
- a second performance run is launched merely to improve the result;
- dataset provenance is incomplete.

After a valid primary OOS run:
STOP SOFTWARE CHANGES.

## 17. Required Gemini completion report

Report:
1. dataset/source;
2. OOS date range;
3. complete-session count;
4. per-symbol coverage;
5. dataset hashes;
6. frozen config hash;
7. execution code SHA;
8. V2-A/B/C results;
9. tactical contribution;
10. margin usage;
11. behavior comparison versus historical V2;
12. interpretation class;
13. tests/lint/doctor results;
14. proof that no parameter was tuned after OOS exposure;
15. exact artifact paths.

Never call the Reddit strategy validated from this phase alone.
