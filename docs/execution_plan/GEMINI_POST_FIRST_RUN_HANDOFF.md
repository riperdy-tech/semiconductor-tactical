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


## Phase L.2 — Final Provenance, Margin-Test, and Accounting-Tolerance Fix

After Phase L.1 review, execute:

`docs/execution_plan/REDDIT_V2_PHASE_L2_FINAL_PROVENANCE_AND_MARGIN_TEST_FIX_PLAN.md`

This is the final research-integrity cleanup before the separate research-analysis phase.

Phase L.2 is strictly limited to:

- strengthening the peak-margin-debt test so the reported `result.peak_margin_debt` is causally produced by an actual transaction/execution path;
- adding a negative-control case showing the test does not report debt when the same transaction is cash-funded;
- separating `EXECUTION_CODE_SHA` from `ARTIFACT_COMMIT_SHA` so the report does not contain self-referential or ambiguous Git provenance;
- making Markdown and JSON carry the same explicit provenance;
- making accounting tolerance explicit and aligning report wording with the declared tolerance;
- adding a Phase L preservation-note erratum without modifying the preserved `PHASE_L_PRESERVATION_NOTE.md`;
- performing a frozen reproducibility rerun only when necessary to establish the final provenance chain.

The following are forbidden in Phase L.2:

- changing any V2 signal parameter;
- changing the 60% normalized core allocation;
- changing MU/SNDK/SKHY scope;
- changing tactical sizing;
- changing slippage, commission, financing, maintenance, or leverage assumptions;
- forcing historical margin usage;
- adding options or Level-2;
- expanding the universe;
- tuning against the July–September result, Reddit-reported P&L, or reported trade count.

### Provenance convention

Use:

`EXECUTION_CODE_SHA` = the exact committed code/test SHA used to execute the historical run.

`ARTIFACT_COMMIT_SHA` = the later commit containing the final generated report/JSON and evidence artifacts.

Do not attempt to place the final artifact commit SHA inside the artifact that defines that same commit.

### Historical preservation

The Phase L preserved note at:

`reports/fidelity_runs/phase_l_baseline_0ce2208/PHASE_L_PRESERVATION_NOTE.md`

must remain unchanged as historical evidence.

Create an adjacent erratum identifying its stale accounting metadata and reconciling it to the preserved Phase L canonical report/JSON.

### Acceptance requirement

Phase L.2 is accepted only when:

- the peak-margin test creates debt through the actual execution path and the backtest result captures it;
- the negative control does not falsely report positive peak debt;
- execution-code and artifact commit SHAs are explicit and consistent;
- accounting tolerance is explicit and tested;
- Markdown and JSON agree;
- preserved Phase K, Phase L, and Phase L.1 evidence remains distinguishable;
- the full test suite and Ruff pass;
- the frozen historical rerun, if required, is deterministic;
- global epistemic statuses remain unchanged.

After Phase L.2 passes:

**STOP SOFTWARE CHANGES.**

The next step is a separately approved research-analysis phase.


## Phase L.2.1 — Final Provenance Taxonomy & Accounting-Tolerance Test Fix

After Phase L.2 review, execute:

`docs/execution_plan/REDDIT_V2_PHASE_L2_1_FINAL_PROVENANCE_TAXONOMY_AND_TOLERANCE_TEST_PLAN.md`

This is the final cleanup for two narrow issues only:

1. replace the ambiguous generic artifact SHA with three explicit provenance concepts:
   - `EXECUTION_CODE_SHA` = exact implementation/test commit executed;
   - `ARTIFACT_CONTENT_COMMIT_SHA` = commit that published the generated historical artifacts;
   - `PROVENANCE_FINALIZATION_COMMIT_SHA` = later commit that finalized the embedded provenance metadata;
2. strengthen the accounting-tolerance regression test so it proves all three cases:
   - below tolerance -> accepted;
   - exactly at tolerance -> accepted;
   - above tolerance -> rejected.

Current Phase L.2 provenance values are:

- Execution code: `c10f91c`
- Artifact content: `d617f53`
- Provenance finalization: `aaa10b5`

Do not collapse these into one generic artifact SHA.

Do not change:

- any V2 signal parameter;
- the 60% core assumption;
- MU/SNDK/SKHY universe;
- tactical sizing;
- slippage/commission/financing/margin assumptions;
- historical dataset;
- historical run economics;
- Phase K/L/L.1 preserved artifacts.

A frozen historical rerun is NOT required merely for this taxonomy/test correction. Only regenerate the canonical report/JSON when mechanically required by the schema change, and do not create a new strategy run unnecessarily.

Required unchanged historical values:

- V2-A: +6.48% / $106,482.16
- V2-B: +7.93% / $107,928.85
- V2-C: +7.93% / $107,928.85
- Tactical contribution: +$1,446.69
- Historical V2-C peak margin debt: $0.00
- Reconciliation discrepancy: $0.000200
- Accounting tolerance: $0.001000

After L.2.1 acceptance criteria pass:

**STOP SOFTWARE CHANGES.**

The next step is a separately approved research-analysis phase.

## Phase L.2.1.1 — Final Artifact Schema Cleanup

After Phase L.2.1 review, execute:

`docs/execution_plan/REDDIT_V2_PHASE_L2_1_1_FINAL_ARTIFACT_SCHEMA_CLEANUP.md`

This is a final, surgical schema cleanup.

The only remaining defect is that the active result model/JSON still retains the ambiguous generic field:

`artifact_commit_sha`

Remove it completely from the active model, serialization, report-generation path, canonical JSON, and active tests.

The final active provenance contract is:

- `execution_code_sha = c10f91c`
- `artifact_content_commit_sha = d617f53`
- `provenance_finalization_commit_sha = aaa10b5`
- `git_sha = c10f91c` only as an explicitly deprecated compatibility alias, if retained
- `artifact_commit_sha = ABSENT`

The package contains the exact required searches, expected diff, targeted/full verification commands, historical invariants, commit discipline, and completion-report format.

Do NOT rerun `fidelity-v2-historical`.

Do NOT change any historical economics, strategy logic, parameters, universe, costs, margin behavior, dataset, or preserved artifacts.

After Phase L.2.1.1 passes:

**STOP SOFTWARE CHANGES.**

The next step is a separately approved research-analysis phase.

# Post-L.2 Research Analysis Tracks

The software engineering/audit freeze is complete.

The next work is research-only and is governed by:
docs/execution_plan/REDDIT_V2_THREE_TRACK_RESEARCH_COORDINATION_PLAN.md

Detailed execution instructions:

## Phase M — Frozen Prospective OOS Validation

Execute:
docs/execution_plan/REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md

Primary question:

Does the frozen V2 directional/core/margin hypothesis generalize to genuinely unseen U.S.-market data after 2026-09-30?

Hard rule:
Do not tune after OOS data exposure.

The historical Run 24a9e783 remains immutable.

## Phase N — V2-D Covered-Call Reconstruction

Execute:
docs/execution_plan/REDDIT_V2_V2D_OPTIONS_EXECUTION_PLAN.md

Primary question:

What incremental economics and risk are produced by the covered-call behavior described by the source, using authentic point-in-time historical option quotes?

Hard rules:
- real historical bid/ask data only;
- no synthetic Black-Scholes headline fills;
- no parameter tuning after performance exposure;
- V2-C remains the immutable control.

## Phase O — V2-F Genuine Level-2 Information-Set Ablation

Execute:
docs/execution_plan/REDDIT_V2_V2F_LEVEL2_EXECUTION_PLAN.md

Primary question:

Does genuine order-book information add decision value to the already-frozen V2 sequence?

Hard rules:
- genuine historical Level-2/order-book data only;
- no synthetic order book from OHLCV;
- primary experiment changes only decision information;
- keep execution economics identical between control and treatment;
- no OOS threshold tuning.

## Cross-track contamination rule

Before viewing new OOS performance, freeze all three research specifications.

Data acquisition and structural data validation may proceed in parallel.

Performance-driven parameter changes are prohibited.

Do not use Phase M results to choose Phase N or O parameters.
Do not use Phase N results to choose Phase O parameters.
Do not shift the common OOS period because one dataset has better results.

If a genuine implementation defect is discovered after performance exposure:
1. preserve the failed run;
2. document the defect;
3. repair it;
4. create a new execution commit;
5. rerun with a new run ID;
6. do not overwrite the previous artifact.

Global statuses remain:

FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED
TRUE_LEVEL2_REPLICATION = UNVALIDATED
HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED
DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2
PRISTINE_OOS = UNAVAILABLE until an unseen chronological period is actually evaluated.

After Phases M/N/O pass their individual gates:

STOP SOFTWARE CHANGES.

The next step is cross-track synthesis and falsification analysis.

# Phase M Post-Run Audit / Provenance Repair

The first prospective run `bb0887e4` is a valid chronological observation but has only two complete sessions and is therefore **NEUTRAL / INCONCLUSIVE**.

Before continuing prospective monitoring, execute:

`docs/execution_plan/REDDIT_V2_PHASE_M_POST_RUN_AUDIT_AND_PROVENANCE_REPAIR_PLAN.md`

This is an infrastructure/audit repair only.

Hard rules:

- preserve `bb0887e4` exactly as an observed two-session result;
- do not rerun the same performance window merely to regenerate artifacts;
- do not tune any V2 parameter;
- do not alter the historical control `24a9e783`;
- use explicit `EXECUTION_CODE_SHA`, `ARTIFACT_CONTENT_COMMIT_SHA`, and `PROVENANCE_FINALIZATION_COMMIT_SHA`;
- do not introduce or retain a generic active `artifact_commit_sha`;
- harden chronological continuation and artifact overwrite protections;
- record exact pytest/Ruff/doctor/doctor-data verification results;
- future OOS observations must use genuinely new chronology and a new run ID.

After this repair, continue Phase M monitoring only as new market sessions become available. Do not use the two-session OOS result to tune Phase N or Phase O.

# Phase M.1.1 — Continuation / Provenance Repair Required

Phase M.1 improved the OOS report/schema but is **not yet accepted**.

Execute:
`docs/execution_plan/REDDIT_V2_PHASE_M1_1_CONTINUATION_AND_PROVENANCE_FINALIZATION_REPAIR_PLAN.md`

Three concrete repairs are required:

1. Verify and correctly classify the actual post-run provenance-finalization commit; expected to distinguish the original artifact commit from the M.1 finalization commit.
2. Run `doctor-data` explicitly against `data/processed_oos` with `configs/v2_oos_frozen.yaml`; the default historical-data doctor result is insufficient.
3. Wire the existing continuation chronology/lineage controls into the canonical CLI and remove the hardcoded 2026-10-01 restriction for legitimate forward continuation runs while preserving the initial-run freeze.

Hard rules:

- **Do not rerun performance for `bb0887e4`.**
- **Do not change any V2 strategy parameter.**
- Preserve `bb0887e4` economic results exactly.
- Preserve historical Run `24a9e783`.
- Do not overwrite accepted artifacts.
- After M.1.1 acceptance, stop software changes and continue only with genuinely new prospective chronology.

# Phase M.1.2 — Provenance Seal and Remote Synchronization

M.1.1 implementation appears functionally complete, but its reported final commit `e84e681` is not yet present on the GitHub remote, and the provenance-finalization field requires a non-self-referential sealing convention.

Execute:

`docs/execution_plan/REDDIT_V2_PHASE_M1_2_PROVENANCE_SEAL_AND_REMOTE_SYNC_PLAN.md`

Hard rules:

- no performance rerun of `bb0887e4`;
- no V2 strategy changes;
- preserve the two-session economic result exactly;
- verify actual Git ancestry for all provenance roles;
- do not claim a commit as finalization if the artifact did not contain that value in that commit;
- complete a non-self-referential provenance seal;
- push the final implementation/sealing commits to `origin/main`;
- verify local HEAD equals remote origin/main;
- re-run only verification suites and the explicitly targeted OOS `doctor-data`.

After M.1.2 acceptance, freeze the engineering/audit layer and return to genuine new chronological OOS monitoring / Phases N and O.

# Phase M.1.3 — Frozen-Config Continuation Date Override

M.1.2 is functionally sealed, but one operational continuation gap remains: the canonical runner still obtains its observation start/end only from `configs/v2_oos_frozen.yaml`.

Execute:

`docs/execution_plan/REDDIT_V2_PHASE_M1_3_FROZEN_CONFIG_CONTINUATION_DATE_OVERRIDE_PLAN.md`

Goal:

- keep `configs/v2_oos_frozen.yaml` immutable;
- keep the initial 2026-10-01 boundary immutable;
- allow future continuation runs to supply explicit forward `--start` / `--end` dates;
- preserve all strategy/cost/universe/margin parameters;
- continue using prior-run lineage and new run IDs.

Hard rules:

- no performance rerun of `bb0887e4`;
- no modification of frozen YAML;
- no strategy tuning;
- verification/unit tests only;
- after M.1.3 acceptance, stop software changes.

