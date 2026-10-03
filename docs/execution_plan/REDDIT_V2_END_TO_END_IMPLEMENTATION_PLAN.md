# Gemini Execution Plan — Reddit Behavioral V2 End-to-End Implementation & Research Gate

## Objective

Turn the existing Phase J V2 architecture into a runnable end-to-end historical research implementation without pretending that the Reddit trader's exact discretionary rules have been recovered.

This phase has two goals:
1. Correct the remaining research-specification issues in V2.
2. Connect the V2 behavioral model to verified U.S.-market historical data so V2-A, V2-B, and V2-C can actually execute.

Do not implement covered-call P&L without validated historical option chains.
Do not claim true Level-2 replication without historical Level-2 data.
Do not model direct KRX or Tokyo execution.
Do not optimize parameters against July–September 2026.

## 1. Read first

Read the existing AGENTS.md, Reddit source notes, V2 evidence matrix, V2 directional behavior, V2 U.S. universe, V2 portfolio model, V2 Level-2 gate, V2 parameter registry, V2 results protocol, Phase H/Phase I integrity plans, preserved baseline, current backtest engine, V2 portfolio engine, execution simulator, data manifest, configs/historical_1m.yaml, and prior run manifests/reports.

Also re-check the primary Reddit post/comments before making any source classification.

## 2. Hard research-integrity rules

For this phase:

- no optimization loops;
- no fitting to $550k;
- no fitting to ~1,300 trades;
- no tuning for positive July–September P&L;
- no selecting an ETF because it improves the result;
- no selecting a core allocation because it improves the result;
- no changing signal thresholds after seeing V2 results.

July–September 2026 remains POST_HOC_HOLDOUT and is not pristine OOS.

## 3. Phase K-A — Correct V2 evidence labels

Several V2 registry items are not truly OBSERVED. Correct them before further implementation.

Reclassify:
- 2.0x account-level gross leverage: ASSUMPTION / HYPOTHESIS. The source supports margin and 2x products, not an exact account gross-leverage cap.
- 50% tactical scale-out: HYPOTHESIS. The source supports active scaling, not a universal 50% rule.
- 3/5/7 DTE: ASSUMPTION / HYPOTHESIS. "Short-dated" does not establish these exact values.
- 50% option decay / 2% underlying-drop repurchase: HYPOTHESIS / ASSUMPTION.
- 60% core allocation: ASSUMPTION.
- monthly core rebalance: ASSUMPTION.
- 25% maintenance ratio: DERIVED/BROKER-MODEL ASSUMPTION, not Reddit-specific.
- 5% margin interest: ASSUMPTION.

Keep source observations such as margin usage, covered-call use, stop-limit use, and Level-2 use as OBSERVED only at the behavioral level actually supported by the source.

## 4. Phase K-B — Freeze the normalized core methodology

Use a normalized core + tactical overlay experiment.

The source does not disclose exact starting weights. Therefore use the already registered 60% core allocation as a research scenario assumption, not as a recovered Reddit account fact.

Default V2 starting state:
- 60% of normalized initial equity allocated to persistent core;
- remaining 40% retained as tactical/liquidity capacity;
- core instruments: MU, SNDK, SKHY;
- equal notional allocation across those three unless a primary-source allocation is established;
- no KXIAY in the default core;
- no candidate leveraged ETF in the default core;
- no USD in the source-replication headline.

Do not invent a monthly rebalance. Keep core static unless altered by tactical interaction, covered-call assignment, or margin liquidation.

Document clearly:
"The 60% normalized core allocation is a research assumption chosen because the source describes persistent large holdings but does not disclose exact starting weights."

## 5. Phase K-C — Candidate leveraged products

Separate:
1. SOURCE_IDENTIFIED leveraged products, only when primary source evidence identifies the exact ticker;
2. CANDIDATE_PROXY products such as SKUU, SKHU, SKHL, MUU, SNDG, SNDU, SNXX.

The default V2-A/B/C headline universe must be:
MU + SNDK + SKHY.

Do not include USD in the source-replication headline.

Do not choose candidate 2x products based on performance.

## 6. Phase K-D — Implement the actual V2 directional signal engine

The current V2 portfolio engine is state/account logic. Create a real signal/order-generation module for the behavioral sequence:

higher-timeframe context
-> directional impulse
-> retreat/pullback
-> stabilization/reclaim
-> tactical add/reload
-> partial reduction
-> full reduction
-> possible re-entry

Each stage must be a separate deterministic predicate/function and carry an evidence label.

## 7. Phase K-E — Use the frozen V2 parameter family

Use only the already registered V2 family from REDDIT_V2_PARAMETER_REGISTRY.md.

Current candidates:
- impulse lookback: 15/30/60 minutes;
- impulse magnitude: 1.5%/2.0%/2.5%;
- pullback depth: 0.382/0.500/0.618;
- stabilization bars: 3/5/8;
- tactical scale-out: 50% or 100%;
- stop mode: LOCAL_LOW or ATR_TRAILING.

Do not grid-search these on July–September.

For the first diagnostic execution, designate one pre-registered default candidate using documented economic rationale before running. Do not change it after observing the result.

## 8. Phase K-F — Default V2 directional behavior

Use one frozen default configuration:
- impulse lookback: 30 minutes;
- impulse magnitude: 2.0%;
- pullback depth: 0.500;
- stabilization: 5 bars;
- tactical scale-out: 50%;
- stop mode: LOCAL_LOW.

These remain HYPOTHESIS/ASSUMPTION proxies, not Reddit-observed rules.

Do not optimize them.

## 9. Phase K-G — Tactical position semantics

Support:
- add;
- reload;
- 50% partial reduction;
- full reduction on documented invalidation/cleanup;
- re-entry.

Core invariant:
A tactical reduction must never automatically liquidate or alter persistent core inventory.

## 10. Phase K-H — Default tactical exit semantics

Use LOCAL_LOW as the first registered stop mode.

Define a deterministic stop below the stabilization/retracement invalidation point with a fixed, pre-registered buffer. Do not determine that buffer from the July–September result.

For the first tactical reduction, use one deterministic rebound condition selected before the run and documented in the V2 spec, such as reclaim of VWAP or return toward the prior impulse zone.

Do not reuse Phase H 1.5x/2.5x ATR parameters.

Do not add extra exits until a separate experiment is approved.

## 11. Phase K-I — Wire signals into the portfolio/execution stack

The required path is:

historical bars
-> feature calculation
-> V2 signal generation
-> order generation
-> ExecutionSimulator
-> V2PortfolioEngine
-> margin/core/tactical state
-> equity curve
-> component attribution

Do not leave V2 as a disconnected portfolio toy model.

Use the existing deterministic execution semantics and no-lookahead rules.

## 12. Phase K-J — Build the V2 historical runner

Add a canonical CLI mode such as fidelity-v2-historical and wire it into run.ps1.

Runner requirements:
1. load verified historical data;
2. load the V2 instrument manifest;
3. reject direct KRX/Tokyo symbols;
4. verify MU/SNDK/SKHY;
5. initialize the normalized 60% core;
6. generate V2 signals;
7. execute tactical orders;
8. track account-level margin;
9. calculate equity;
10. emit JSON + Markdown;
11. persist config hash, manifest/hash, git SHA, universe, and scope classification;
12. label July–September results POST_HOC_HOLDOUT.

Do not silently include USD, KXIAY, or candidate leveraged ETFs.

## 13. Phase K-K — Execute V2-A/B/C only

V2-A — Core only:
- persistent MU/SNDK/SKHY normalized core;
- no tactical sleeve.

V2-B — Core + tactical:
- same core;
- deterministic tactical add/reduce/re-entry;
- no additional account leverage beyond the registered normalized setup.

V2-C — Core + tactical + margin:
- same frozen V2-B behavior;
- account-level margin and financing.

Do not execute V2-D covered calls until authentic option-chain data is validated.
Do not execute V2-E full composite until all required components are validated.
Do not execute V2-F Level-2 ablations without true Level-2 data.

## 14. Phase K-L — Default universe must stay clean

Headline V2-A/B/C:
MU, SNDK, SKHY only.

Explicitly exclude:
USD, SKUU, SKHU, SKHL, MUU, SNDG, SNDU, SNXX, KXIAY.

Candidate proxy experiments are separate research artifacts only.

## 15. Phase K-M — Data gates

For V2-A/B/C require verified:
- MU;
- SNDK;
- SKHY;
- benchmarks needed by the chosen trend proxy.

Keep these statuses explicit:
TRUE_LEVEL2_REPLICATION = UNVALIDATED
HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED
DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2
PRISTINE_OOS = UNAVAILABLE

## 16. Phase K-N — Required metrics

Report separately:

Core:
- starting value;
- ending value;
- realized/unrealized P&L;
- turnover.

Tactical:
- gross/net P&L;
- trade count;
- adds/reloads;
- partial/full exits;
- re-entries;
- win rate;
- expectancy;
- holding-time distribution.

Account:
- total return;
- max drawdown;
- gross/net exposure;
- margin debt;
- margin interest;
- margin utilization;
- margin calls;
- forced liquidations.

Costs:
- signal-price/pre-slippage P&L;
- execution slippage;
- commissions;
- financing;
- net realized P&L;
- portfolio net P&L.

Reconcile these without double-counting.

## 17. Phase K-O — Plausibility diagnostics

Report:
- trades/session;
- median and distribution of holding times;
- core investment percentage;
- tactical time in market;
- concurrent positions;
- tactical turnover;
- average add/reload size;
- tactical allocation as a percentage of total equity.

These are descriptive checks only and must never be optimized toward the Reddit trade count.

## 18. Phase K-P — Historical result scope

If V2-A/B/C are run on July–September:
- classify as POST_HOC_HOLDOUT;
- do not call them OOS validation;
- state that the V2 parameters were frozen before the V2 result, but the underlying date range had already been inspected by earlier research phases.

## 19. Phase K-Q — Future OOS

Do not move or select the OOS boundary based on performance.

After V2 implementation and parameters are frozen, the next genuinely unseen chronological data becomes the only valid pristine-OOS candidate.

If unavailable:
PRISTINE_OOS = UNAVAILABLE.

## 20. Tests

Add tests for:
- default V2 signal sequence;
- impulse detection;
- pullback;
- stabilization/reclaim;
- tactical add/reload;
- partial/full tactical reduction;
- re-entry;
- core isolation;
- margin;
- no-lookahead;
- pending order behavior;
- clean default universe;
- 60% normalized core initialization;
- P&L attribution;
- no double-counting;
- reproducible run manifest;
- POST_HOC_HOLDOUT labeling.

Run:
.\run.ps1 test
.\run.ps1 doctor
.\run.ps1 doctor-data -Config configs/historical_1m.yaml -DataDir data/processed
.\.venv\Scripts\python.exe -m ruff check .

## 21. Required documentation

Create/update:
- docs/execution_plan/REDDIT_V2_END_TO_END_IMPLEMENTATION.md
- docs/execution_plan/REDDIT_V2_HISTORICAL_RUN_PROTOCOL.md
- docs/REDDIT_V2_DIRECTIONAL_BEHAVIOR.md
- docs/execution_plan/REDDIT_V2_PARAMETER_REGISTRY.md
- docs/execution_plan/REDDIT_V2_RESULTS_PROTOCOL.md
- docs/DECISIONS.md

Explicitly document that 60% core is an assumption and V2-A/B/C are U.S.-market equity/margin experiments, not full Reddit replication.

## 22. Definition of done

- V2 evidence labels corrected;
- account-level leverage no longer labeled OBSERVED;
- 50% scaling no longer labeled OBSERVED;
- exact DTE/repurchase thresholds no longer labeled OBSERVED;
- 60% core allocation explicitly ASSUMPTION;
- monthly rebalance removed from default behavior unless separately justified;
- normalized core initialization implemented;
- V2 directional signal engine exists as real code;
- V2 signal generation is wired into ExecutionSimulator;
- V2 orders are processed by V2PortfolioEngine;
- V2 historical runner exists and is exposed by run.ps1;
- default V2-A/B/C universe is MU/SNDK/SKHY only;
- USD is excluded from the source-replication headline;
- candidate leveraged products are isolated;
- KXIAY excluded until data validation;
- options and Level-2 remain data-gated;
- V2-A/B/C execute end-to-end reproducibly;
- provenance is persisted;
- July–September is POST_HOC_HOLDOUT;
- no optimization occurred;
- tests and ruff pass.

## 23. Mandatory stop condition

After V2-A/B/C can execute reproducibly and all acceptance criteria pass:

STOP SOFTWARE CHANGES.

Do not optimize the V2 parameters, core percentage, exit trigger, ETF selection, KXIAY inclusion, trade count, or July–September profitability.

The next step is a separately approved research-analysis phase.

## 24. Research question

The next research question is:

"Does active tactical trading around a persistent MU/SNDK/SKHY core portfolio add positive net economic value after realistic execution costs and margin financing, without relying on covered calls, direct Asian-market execution, or Level-2 data that we cannot yet validate?"

If V2-B is negative, that informs the equity tactical layer.
If V2-B is positive but V2-C mainly amplifies outcomes, that separates signal edge from leverage.

Do not interpret V2-A/B/C as a complete test of the Reddit trader's claimed $550k result.
