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

This is the substantive V2 architecture/specification phase.

V2 must model the Reddit source as a portfolio process rather than a single buy/sell signal, including persistent core holdings, tactical add/reduce/re-entry, account-level margin, covered calls attached to owned shares, stop-limit execution, a Level-2 data gate, and U.S.-market-only execution.

V2 scope excludes direct KRX and Tokyo execution. The default headline universe is MU/SNDK/SKHY. KXIAY and candidate U.S.-listed 2x products remain separate, explicitly labeled proxy experiments until data and source-evidence gates pass.

Do not optimize for $550k, ~1,300 trades, or positive P&L.

## Phase K — Reddit Behavioral V2 End-to-End Implementation & Research Gate

After Phase J and Phase I pass, execute:

docs/execution_plan/REDDIT_V2_END_TO_END_IMPLEMENTATION_PLAN.md

This phase is the bridge from V2 architecture to a real historical backtest.

It must first correct remaining evidence labels:

- account-level 2.0x gross leverage is an ASSUMPTION/HYPOTHESIS, not OBSERVED;
- 50% tactical scale-out is HYPOTHESIS, not OBSERVED;
- exact 3/5/7 DTE values are ASSUMPTION/HYPOTHESIS, not OBSERVED;
- exact numerical option repurchase triggers are HYPOTHESIS/ASSUMPTION;
- 60% normalized core allocation is an ASSUMPTION;
- monthly core rebalance is not part of the default V2 behavior unless separately justified.

Then:

- freeze a normalized 60% core research scenario across MU/SNDK/SKHY;
- keep candidate leveraged products separate from the headline replication;
- implement a real V2 directional signal/order-generation module;
- connect signals to ExecutionSimulator and V2PortfolioEngine;
- add a canonical V2 historical runner and run.ps1 mode;
- execute only V2-A, V2-B, and V2-C in the first end-to-end historical pass;
- keep covered calls blocked pending real option-chain data;
- keep Level-2 blocked pending genuine historical Level-2 data;
- keep direct KRX/Tokyo execution out of scope;
- preserve POST_HOC_HOLDOUT classification for July–September;
- do not reuse or retune Phase H post-hoc parameters.

The first V2 historical diagnostic must use the pre-registered default candidate defined in the V2 registry and must not perform a July–September parameter search.

After V2-A/B/C execute reproducibly and all acceptance criteria pass:

STOP SOFTWARE CHANGES.

The next step is a separately approved research-analysis phase.

Global status must remain:

FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED
TRUE_LEVEL2_REPLICATION = UNVALIDATED
HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED
DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2
PRISTINE_OOS = UNAVAILABLE



## Phase L — Reddit Behavioral V2 Post-Run Audit & Accounting Correction

After Phase K, execute:

docs/execution_plan/REDDIT_V2_POST_RUN_AUDIT_AND_ACCOUNTING_PLAN.md

This phase is a narrow research-integrity audit of the completed V2-A/B/C implementation. It is not a strategy-improvement or optimization phase.

The Phase K historical result must remain preserved as the original evidence artifact. Phase L may correct implementation/accounting defects and rerun the same frozen historical experiment, but it must not retune the Reddit-inspired behavior.

Phase L must specifically audit and, where necessary, correct:

- the true V2 evaluation start because SKHY begins later than MU/SNDK;
- the semantics of the normalized 60% core starting state;
- reference-price versus execution-price semantics in the ExecutionSimulator;
- the current pre_slippage_pnl field, which must be based on an unadjusted reference price rather than an already-slippage-adjusted execution price;
- exact single-count treatment of slippage, commissions, and financing;
- separation of closed tactical P&L from terminal open tactical mark-to-market P&L;
- reconciliation of entry fills, reloads, exits, completed round trips, and open tactical inventory;
- no-lookahead buying-power and capital checks for orders filled at the next bar open;
- no-lookahead timing for margin-triggered liquidation;
- peak margin debt measurement after transactions/financing, not only before them;
- core/tactical attribution and core isolation.

Important interpretation rule:

A historical V2-C result identical to V2-B is acceptable when margin was never actually required. Do not modify historical sizing to force leverage. Instead, add a synthetic engine test proving that V2-C margin debt, financing, maintenance, and tactical-first liquidation machinery works when deliberately exercised.

Phase L must preserve:

FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED
TRUE_LEVEL2_REPLICATION = UNVALIDATED
HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED
DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2
PRISTINE_OOS = UNAVAILABLE

After Phase L acceptance criteria pass:

STOP SOFTWARE CHANGES.

The next step is a separately approved research-analysis phase.


## Phase L.1 — V2 Accounting Reconciliation & Reproducibility Fix

Phase L implementation exposed a remaining research-accounting defect: the canonical Phase L report can include slippage on terminal open tactical inventory in a total slippage figure while comparing that total against closed FIFO reference P&L. This can create a mismatch between closed gross reference P&L, reported slippage, and closed realized P&L.

Execute:

docs/execution_plan/REDDIT_V2_PHASE_L1_RECONCILIATION_FIX_PLAN.md

This is a strict accounting/reproducibility correction only.

Do not change:
- any frozen V2 signal parameter;
- the 60% core assumption;
- MU/SNDK/SKHY universe;
- tactical sizing;
- slippage/commission assumptions;
- margin assumptions;
- research scope.

Phase L.1 must:
- preserve the Phase K artifact;
- preserve the Phase L pre-correction artifact;
- separate closed-trade slippage from open-position entry slippage;
- reconcile closed reference P&L exactly to closed realized P&L;
- reconcile open reference MTM exactly to open terminal contribution;
- count commissions and financing exactly once;
- make Markdown and JSON agree;
- eliminate stale contradictory completion-summary metrics;
- strengthen the buying-power no-lookahead test so it exercises the actual accept/reject decision;
- strengthen the margin liquidation test so it proves next-bar execution rather than merely order creation;
- strengthen the peak-margin test so it proves debt created by a transaction is included in peak debt;
- rerun the historical result only when necessary to produce corrected artifacts, with the exact same frozen strategy configuration.

The checked-in machine-readable artifact is authoritative. The final Gemini report must match it exactly.

Global status remains:

FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED
TRUE_LEVEL2_REPLICATION = UNVALIDATED
HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED
DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2
PRISTINE_OOS = UNAVAILABLE

After Phase L.1 acceptance criteria pass:

STOP SOFTWARE CHANGES.

The next step is a separately approved research-analysis phase.
