# Gemini Execution Plan — V2-D Historical Covered-Call Reconstruction

## 0. Objective

Build and validate the missing covered-call component of Reddit Behavioral V2.

Repository definition:
V2-D = Core + Tactical + Margin + Covered Calls.

Research questions:
1. Can authentic historical option data support executable covered-call reconstruction?
2. How much incremental P&L does the covered-call layer contribute versus frozen V2-C?
3. How does the option layer change drawdown, exposure, assignment, and capital usage?

Do not claim full Reddit replication.

## 1. Hard gates

V2-D cannot become a validated headline result unless all of the following are satisfied:
- authentic historical option quotes;
- point-in-time timestamps;
- bid and ask;
- contract identity;
- strike;
- expiration;
- call/put type;
- underlying symbol;
- underlying price;
- contract multiplier;
- quote conditions;
- underlying-share synchronization;
- adjustment/corporate-action policy;
- sufficient chain coverage;
- deterministic contract selection;
- deterministic buyback rule;
- assignment/liquidation handling;
- provenance and hashing;
- no lookahead.

Synthetic Black-Scholes prices are forbidden for headline execution.

Midpoint-only execution is not the primary executable result. It may only be used as a separate sensitivity diagnostic.

## 2. Read first

Read:
1. AGENTS.md
2. docs/REDDIT_SOURCE_NOTES.md
3. docs/REDDIT_BEHAVIORAL_V2_EVIDENCE_MATRIX.md
4. docs/REDDIT_V2_DIRECTIONAL_BEHAVIOR.md
5. docs/execution_plan/REDDIT_V2_PARAMETER_REGISTRY.md
6. docs/execution_plan/REDDIT_V2_RESULTS_PROTOCOL.md
7. docs/REDDIT_V2_PORTFOLIO_MODEL.md
8. docs/STRATEGY_SPEC.md
9. src/tactical_engine/options/contracts.py
10. src/tactical_engine/options/chain_provider.py
11. src/tactical_engine/options/covered_calls.py
12. src/tactical_engine/options/assignment.py
13. accepted V2-C historical artifacts.

## 3. Evidence labels

OBSERVED:
- covered calls used;
- short-dated;
- written during strength;
- bought back on pullbacks;
- written against owned shares.

ASSUMPTION / HYPOTHESIS:
- exact DTE;
- exact strike/delta;
- exact contract count;
- exact sell trigger;
- exact buyback threshold;
- exact early-assignment behavior;
- exact interaction between tactical shares and covered shares.

Never promote assumptions to OBSERVED.

## 4. Preserve V2-C as immutable control

V2-C remains:
frozen core + frozen tactical + frozen margin.

V2-D is:
exact same V2-C + covered calls.

No other strategy component may change.

The primary incremental quantity is:
V2-D economics minus V2-C economics.

## 5. Option data manifest

Create:
reports/data_manifests/options/v2d_option_data_manifest.json

Include:
- source/vendor;
- product;
- license/usage status;
- retrieval timestamp;
- underlying symbols;
- start/end timestamp;
- quote resolution;
- timestamp precision;
- option symbology;
- strike range;
- expiration coverage;
- bid/ask completeness;
- volume/open interest;
- delta availability;
- underlying-price source;
- corporate-action source;
- per-file SHA256;
- aggregate SHA256.

Preferred data is point-in-time intraday quotes sufficient to reproduce the strength event and subsequent pullback buyback.

End-of-day-only chains are insufficient for the source-described intraday behavior.

## 6. Data-quality gate

Reject or quarantine:
- duplicate timestamps;
- backwards timestamps;
- negative bid/ask;
- ask below bid;
- missing contract metadata;
- impossible expiration;
- wrong multiplier;
- stale quotes outside a documented threshold;
- quotes without a valid synchronized underlying price.

Do not silently drop adverse quotes.

Report exclusions and missing-quote counts.

## 7. Contract lifecycle

Required states:
AVAILABLE -> SOLD -> OPEN -> BOUGHT_BACK
or
AVAILABLE -> SOLD -> OPEN -> EXPIRED/ASSIGNED

At sale:
- execute at bid;
- record premium;
- record quantity;
- record timestamp;
- record covered-share linkage;
- record fees.

At buyback:
- execute at ask;
- record cost and exit timestamp;
- realize option P&L.

At expiry:
- evaluate intrinsic condition;
- either expire worthless or assign;
- assignment must update underlying shares and cash;
- no double counting of delivered shares.

If early assignment cannot be modeled reliably, explicitly set EARLY_ASSIGNMENT_STATUS = UNVALIDATED and do not label the complete V2-D result fully validated.

## 8. Covered-share invariant

At every timestamp:
short-call shares <= eligible long shares.

Add tests for:
- exactly covered;
- under-covered;
- attempted over-write.

Uncovered calls must be rejected.

Tactical inventory must never silently become eligible covered inventory unless the frozen rule explicitly says so.

## 9. Frozen contract-selection policy

Use the candidate family already registered in docs/execution_plan/REDDIT_V2_PARAMETER_REGISTRY.md:
- DTE: 3/5/7 days;
- OTM delta: 0.20/0.30;
- repurchase: 50% premium decay OR 2% underlying drop.

Before any V2-D performance execution, freeze one deterministic default.

Required default for the first research run:
- target DTE: 5 days;
- target OTM delta: 0.20;
- sell maximum fully covered contracts;
- buy back at the first occurrence of either 50% premium decay or 2% underlying decline from the sale reference;
- otherwise hold through expiration/assignment.

These values are HYPOTHESIS/ASSUMPTION.

If the historical vendor does not supply trustworthy historical delta, do not synthesize Black-Scholes delta for the headline result. Either use a documented non-Greek selection rule as a separately pre-registered experiment or stop the headline V2-D path.

## 10. Sell trigger

Use the existing frozen V2 strength/rebound event.

At a valid strength event:
1. determine eligible core shares;
2. request point-in-time option chain;
3. select frozen contract;
4. sell covered quantity at executable bid;
5. record quote timestamp and contract identity.

If no executable quote exists:
- do not fill at mid;
- record NO_EXECUTABLE_OPTION_QUOTE;
- report the missed event.

Do not invent quotes.

## 11. Buyback trigger

Use:
- 50% premium decay OR
- 2% underlying decline.

Evaluation order:
1. obtain point-in-time option quote;
2. test both triggers;
3. if either fires, buy back at executable ask;
4. if both fire, execute one buyback;
5. otherwise remain short.

No future premium may be used to trigger the buyback.

## 12. Costs

Short call entry uses bid.

Buyback uses ask.

Record:
- gross premium;
- gross buyback;
- spread cost;
- commission/fees;
- net option P&L.

Keep option P&L separate from underlying P&L.

## 13. Portfolio integration

Do not build a separate accounting ledger.

Integrate:
V2 directional signal
-> covered-call manager
-> option chain provider
-> execution semantics
-> V2PortfolioEngine

Ledger must reconcile:
- core shares;
- tactical shares;
- call positions;
- premiums;
- buybacks;
- assignments;
- financing;
- fees;
- slippage.

Add explicit incremental attribution:
V2-C economics + net option economics + assignment effects = V2-D economics.

## 14. Primary result design

Primary control:
V2-C.

Primary treatment:
V2-D.

Report:
- final equity;
- net return;
- incremental P&L;
- incremental max drawdown;
- option premium;
- buyback cost;
- assignment/expiry;
- average DTE;
- average moneyness/delta;
- bid/ask spread;
- quote-miss rate;
- covered-share percentage.

Do not claim the option layer proves the trader's exact discretionary rule.

## 15. Contamination and OOS policy

The July–September period remains POST_HOC_HOLDOUT.

The chosen V2-D contract policy must be frozen before performance evaluation.

For a validation claim, use the same unseen future OOS period defined by the V2 frozen OOS plan.

Do not choose DTE, delta, buyback threshold, or coverage ratio after seeing performance.

## 16. Required tests

1. point-in-time chain lookup;
2. no future quote leakage;
3. bid-side sale;
4. ask-side buyback;
5. covered-share cap;
6. over-write rejection;
7. expiration without assignment;
8. expiration assignment;
9. premium accounting;
10. buyback accounting;
11. assignment accounting;
12. underlying-share reconciliation;
13. option/equity P&L separation;
14. no-lookahead between V2 signal and option fill;
15. missing quote produces no fabricated fill;
16. options-disabled V2-C result remains unchanged;
17. V2-D minus V2-C attribution reconciles;
18. option data provenance/hash validation.

## 17. Verification

Run:
- .\run.ps1 test
- .\run.ps1 doctor
- .\.venv\Scripts\python.exe -m ruff check .

Run the option-specific test suite.

Do not run headline V2-D until the data gate passes.

If the data gate fails:
HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED.

## 18. Required artifacts

Create:
- docs/research/v2d/V2D_FROZEN_SPEC.md
- reports/data_manifests/options/v2d_option_data_manifest.json
- reports/v2d/<run_id>.json
- reports/v2d/<run_id>.md
- reports/fidelity_runs/v2d_<run_id>/PRESERVATION_NOTE.md

Statuses:
- GATED_UNVALIDATED
- VALIDATED_PARTIAL
- VALIDATED

Never call V2-D full Reddit replication.

## 19. Stop conditions

STOP if:
- synthetic option prices are proposed;
- Black-Scholes prices are used for headline execution;
- data is not point-in-time;
- covered shares exceed owned shares;
- contract metadata is not auditable;
- early assignment is silently ignored;
- parameters are changed after performance is observed.

## 20. Completion report

Report:
1. source/vendor;
2. data coverage;
3. quote granularity;
4. contract coverage;
5. bid/ask completeness;
6. delta availability;
7. assignment handling;
8. frozen policy;
9. V2-C versus V2-D economics;
10. option incremental contribution;
11. assignment/expiry statistics;
12. missing-quote statistics;
13. tests;
14. hashes;
15. blockers;
16. final status.

Do not call V2-D fully validated merely because the engine runs.
