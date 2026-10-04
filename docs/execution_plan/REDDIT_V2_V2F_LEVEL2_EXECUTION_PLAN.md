# Gemini Execution Plan — V2-F Genuine Level-2 Information-Set Ablation

## 0. Objective

Build the repository's V2-F experiment:

Compare the exact frozen OHLCV V2 strategy against the same strategy augmented with genuine historical Level-2/order-book information.

Scientific question:

Does the information explicitly described by the Reddit trader — order-book depth, bid/ask liquidity, walls, depletion and replenishment — materially change tactical decision quality when every other V2 mechanic is held constant?

V2-F is an information-set ablation, not a strategy redesign.

## 1. Current gate

Current repository status:
TRUE_LEVEL2_REPLICATION = UNVALIDATED

Reason:
OHLCV cannot reconstruct true order-book state and synthetic Level-2 is prohibited.

This phase may change the status only after the data and replay gates below pass.

## 2. Hard research-integrity rules

Forbidden:
- synthesizing a Level-2 book from OHLCV;
- deriving queue depth from minute volume;
- inventing walls from candle highs/lows;
- filling order-book gaps with OHLCV estimates in the headline result;
- tuning Level-2 thresholds on OOS results;
- changing the frozen V2 directional parameters;
- changing the 60% core;
- changing MU/SNDK/SKHY;
- changing cost assumptions to make Level 2 appear beneficial;
- changing the OHLCV control execution semantics;
- claiming full Reddit replication.

Primary control and treatment may differ only in decision information.

## 3. Read first

Read:
1. AGENTS.md
2. docs/REDDIT_SOURCE_NOTES.md
3. docs/REDDIT_BEHAVIORAL_V2_EVIDENCE_MATRIX.md
4. docs/REDDIT_V2_DIRECTIONAL_BEHAVIOR.md
5. docs/execution_plan/REDDIT_V2_LEVEL2_DATA_GATE.md
6. docs/execution_plan/REDDIT_V2_RESULTS_PROTOCOL.md
7. docs/execution_plan/REDDIT_V2_HISTORICAL_RUN_PROTOCOL.md
8. docs/execution_plan/REDDIT_V2_PARAMETER_REGISTRY.md
9. src/tactical_engine/backtest/v2_engine.py
10. src/tactical_engine/signals/v2_signals.py
11. src/tactical_engine/execution/simulator.py
12. src/tactical_engine/portfolio/v2_portfolio.py
13. accepted V2 historical report.

## 4. Level-2 data contract

Create:
reports/data_manifests/level2/v2f_level2_data_manifest.json

Minimum fields:
- vendor/source;
- product;
- licensing status;
- symbol;
- venue;
- timestamp precision;
- timezone;
- message type;
- order ID where available;
- side;
- price;
- size;
- sequence;
- add/cancel/replace/execute;
- snapshot availability;
- depth coverage;
- regular-session coverage;
- per-file SHA256;
- aggregate SHA256.

Preferred source:
genuine MBO or MBP order-book data.

If venue-specific:
- record venue explicitly;
- report venue limitations;
- never call venue-only depth "consolidated Level 2".

## 5. Data-quality validator

Validate:

Ordering:
- timestamps non-decreasing;
- sequence monotonic where supplied;
- no impossible event order.

Book:
- bid < ask;
- non-negative depth;
- valid tick increments;
- valid size.

Lifecycle:
MBO:
- add creates order;
- cancel/replace updates existing order;
- execute reduces order;
- completed orders disappear.

MBP:
- price-level depth changes reconcile.

Session:
- RTH and extended hours separated;
- no silent session mixing.

Coverage:
- per-symbol coverage;
- per-day coverage;
- event counts;
- gaps;
- depth-level availability.

Do not silently delete bad intervals.

## 6. Point-in-time order-book replay

Create a deterministic module such as:
src/tactical_engine/microstructure/order_book.py

Responsibilities:
1. consume events in timestamp order;
2. reconstruct bid/ask ladders;
3. expose top-N levels;
4. calculate spread;
5. calculate depth;
6. calculate imbalance;
7. detect wall persistence;
8. detect depletion;
9. detect replenishment;
10. return a snapshot exactly at the decision timestamp.

The replay must be deterministic from the raw event stream.

No future event may affect a prior snapshot.

## 7. Minimum microstructure feature object

Expose:
- best bid;
- best ask;
- spread;
- top-1 imbalance;
- top-5 imbalance;
- top-5 bid depth;
- top-5 ask depth;
- bid-wall size;
- ask-wall size;
- bid-wall persistence;
- ask-wall persistence;
- bid-depth depletion;
- ask-depth depletion;
- bid replenishment;
- ask replenishment;
- event intensity;
- trade-to-depth ratio.

Every feature record must include:
- symbol;
- timestamp;
- lookback interval;
- source/provenance;
- no-lookahead status.

## 8. Freeze a small Level-2 parameter family

Create:
docs/research/v2f/V2F_MICROSTRUCTURE_PARAMETER_REGISTRY.md

Do not grid-search the OOS period.

Initial default hypothesis:

Imbalance:
top-5 imbalance >= +0.20

where:
imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth)

Spread:
spread <= 2 x minimum tick

Persistence:
positive imbalance must persist for a short pre-registered interval.

Replenishment:
positive bid replenishment must occur after the pullback rather than only during the initial impulse.

The exact persistence/replenishment definitions must be frozen before OOS performance is viewed.

All such values are HYPOTHESIS, not source observations.

## 9. Primary V2-F control/treatment design

Control:
V2_OHLCV_BASELINE

Treatment:
V2_LEVEL2_MICROSTRUCTURE

Identical:
- universe;
- core allocation;
- impulse;
- pullback;
- stabilization;
- exits;
- margin;
- costs;
- execution schedule.

Only the information available to the tactical decision layer changes.

## 10. Keep execution economics constant

For the primary ablation:
- use the same ExecutionSimulator;
- same slippage model;
- same commission model;
- same next-open execution timing.

This isolates information value.

A separate execution-realism experiment may later compare:
- OHLCV cost model;
- quote/order-book-aware cost model.

That experiment must remain separate from primary V2-F.

## 11. Decision semantics

Map Level-2 onto the existing V2 sequence:

impulse -> pullback -> stabilization -> reclaim -> tactical entry

Example deterministic gating:

1. OHLCV detects the existing frozen stabilization event.
2. Read Level-2 snapshot at the decision timestamp.
3. Require positive top-5 imbalance.
4. Require bid replenishment.
5. Require acceptable spread.
6. Allow the existing tactical order.
7. Otherwise reject the existing order.

Level 2 may confirm or veto an existing V2 entry.

Do not create an entirely new trading strategy from order-book observations.

## 12. No-lookahead tests

Prove:
- time-t features use only events <= t;
- t+1 cannot alter t;
- post-decision cancel/execute events cannot change the prior decision;
- execution timing remains unchanged;
- exact-timestamp inclusion policy is explicit.

Add a test where the future book state is deliberately modified and the t decision remains unchanged.

## 13. Development versus final evaluation

July–September may be used for:
- parser tests;
- book reconstruction correctness;
- event lifecycle tests;
- deterministic replay;
- data-quality visualization;
- smoke tests.

Do not use July–September to select final Level-2 thresholds.

Final performance must use the same unseen chronological window defined by the frozen OOS plan.

Freeze:
- feature set;
- threshold values;
- code;
- costs;
- execution semantics;

before OOS performance output is inspected.

## 14. Required ablation metrics

Decision:
- candidate events;
- Level-2 accepted entries;
- Level-2 rejected entries;
- rejection reason;
- time-to-entry;
- re-entry changes.

Performance:
- OHLCV return;
- Level-2 return;
- incremental P&L;
- incremental drawdown;
- tactical P&L;
- win rate;
- expectancy;
- profit factor.

Microstructure:
- spread at decision;
- top-5 imbalance;
- visible depth;
- wall statistics;
- quote rejection rate;
- event intensity.

Robustness:
- symbol;
- day;
- first-half/second-half;
- confidence interval on incremental daily return.

Do not optimize diagnostics.

## 15. Primary causal quantity

V2_LEVEL2_INCREMENTAL_PNL = V2_LEVEL2 - V2_OHLCV

Also report:
- incremental trade count;
- incremental drawdown;
- incremental win rate;
- entry rejection rate.

Do not interpret a positive result as proof that the trader used these exact thresholds.

It tests whether a deterministic Level-2 proxy consistent with the source behavior adds information.

## 16. Level-2 validity classes

UNVALIDATED:
data gate not passed.

DATA_VALIDATED:
raw historical depth passes the structural gate.

ABLATION_VALIDATED:
primary V2-F experiment runs reproducibly with genuine depth and frozen rules.

PARTIAL_MICROSTRUCTURE_REPLICATION:
venue/data coverage is incomplete relative to the source's implied information set.

Never use TRUE_REDDIT_LEVEL2_REPLICATION = VALIDATED unless the evidence actually supports it.

## 17. Required tests

1. event ordering;
2. add/cancel/execute lifecycle;
3. book reconstruction;
4. top-N depth;
5. imbalance;
6. spread;
7. wall persistence;
8. replenishment;
9. event-time no-lookahead;
10. deterministic snapshots;
11. missing-event handling;
12. venue/session separation;
13. identical OHLCV inputs for control/treatment;
14. only decision information differs;
15. V2-A core unchanged;
16. primary ExecutionSimulator unchanged;
17. no future quote can create a fill;
18. data provenance/hash validation.

## 18. Required artifacts

Create:
- docs/research/v2f/V2F_FROZEN_SPEC.md
- docs/research/v2f/V2F_MICROSTRUCTURE_PARAMETER_REGISTRY.md
- reports/data_manifests/level2/v2f_level2_data_manifest.json
- reports/v2f/<run_id>.json
- reports/v2f/<run_id>.md
- reports/fidelity_runs/v2f_<run_id>/PRESERVATION_NOTE.md

If the data gate fails, create only the data-audit artifacts. Never create a fabricated performance result.

## 19. Verification

Run:
- .\run.ps1 test
- .\run.ps1 doctor
- .\.venv\Scripts\python.exe -m ruff check .

Run the microstructure-specific test suite.

Do not run headline V2-F until the genuine Level-2 data gate passes.

## 20. Stop conditions

STOP if:
- Level-2 is synthesized from OHLCV;
- venue limitations are hidden;
- gaps are silently filled;
- thresholds are changed after OOS performance;
- primary execution costs are changed;
- the treatment becomes a new strategy rather than an information ablation;
- future events leak into prior features.

After a reproducible V2-F ablation:
STOP SOFTWARE CHANGES.

## 21. Completion report

Report:
1. source/vendor;
2. venue scope;
3. event type;
4. timestamp precision;
5. coverage;
6. data-quality audit;
7. replay implementation;
8. frozen feature set;
9. frozen thresholds;
10. control result;
11. treatment result;
12. incremental P&L;
13. decision rejection/acceptance;
14. no-lookahead tests;
15. provenance hashes;
16. gate status;
17. remaining limitations.

Do not call V2-F full Reddit replication.
