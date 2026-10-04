# Gemini Execution Plan — Phase L.2 Final Provenance, Margin-Test, and Accounting-Tolerance Fix

## Objective

Close the remaining research-integrity defects identified after Phase L.1 review.

Phase L.2 is a final provenance and test-quality correction. It is NOT a strategy change, optimization pass, parameter search, robustness search, or new behavioral experiment.

The target is to make the checked-in V2 historical evidence package internally auditable and to make the peak-margin test prove the claim it currently purports to prove.

## Hard stop / scope rules

Do NOT:

- change any V2 directional parameter;
- change the 60% normalized core allocation;
- change the MU/SNDK/SKHY headline universe;
- change tactical sizing;
- change slippage, commission, financing, maintenance, or leverage assumptions;
- add covered calls;
- add Level-2;
- add KRX/Tokyo execution;
- expand the universe for performance;
- tune against July–September 2026;
- optimize for the Reddit-reported $550k profit or ~1,300 trades;
- modify the historical strategy merely to force margin usage;
- overwrite or rewrite the preserved Phase K or Phase L evidence artifacts.

Historical reruns are allowed only when needed to establish final reproducibility/provenance under the corrected implementation. Any rerun must use the exact frozen V2 configuration and the same dataset.

## 1. Read first

Read:

1. `docs/execution_plan/REDDIT_V2_PHASE_L1_RECONCILIATION_FIX_PLAN.md`
2. `docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md`
3. `reports/V2_HISTORICAL_COMPARISON.md`
4. `reports/v2_historical_comparison.json`
5. `reports/fidelity_runs/phase_l_baseline_0ce2208/`
6. `src/tactical_engine/portfolio/v2_portfolio.py`
7. `src/tactical_engine/backtest/v2_engine.py`
8. `src/tactical_engine/execution/simulator.py`
9. the V2 historical runner/report-generation code;
10. the exact Phase L.1 implementation commit and test suite.

Before editing, record the current Phase L.1 implementation SHA and current report/artifact SHAs.

## 2. Preserve Phase L.1 evidence before editing

Create an immutable Phase L.1 preservation record before modifying any existing artifact.

Required classification:

- `PHASE_K_REPORTED_RESULT`
- `PHASE_L_REPORTED_RESULT`
- `PHASE_L1_CORRECTED_RESULT`
- `PHASE_L2_FINAL_REPRODUCED_RESULT` for the eventual final run, if a rerun is performed.

Do not silently rewrite the old Phase L preservation note.

The existing `PHASE_L_PRESERVATION_NOTE.md` contains stale/wrong Phase L accounting metadata relative to the preserved canonical Phase L report. Do NOT edit that historical note in place. Instead, create an adjacent erratum, for example:

`reports/fidelity_runs/phase_l_baseline_0ce2208/PHASE_L_PRESERVATION_NOTE_ERRATA.md`

The erratum must:

- preserve the original note as historical evidence;
- identify the specific stale fields;
- state the corrected values from the preserved Phase L report/JSON;
- explain that the erratum is metadata correction only and does not alter the preserved Phase L run.

At minimum, reconcile the stale note's claims about:
- tactical realized P&L;
- total slippage;
- closed reference P&L.

Use the preserved Phase L report/JSON as the authoritative source for those historical values.

## 3. Primary test defect — actually prove peak margin debt

The current `test_peak_margin_debt_sampled_after_transactions` is insufficient.

It manually constructs a portfolio state containing debt, but the separate backtest result only asserts a non-negative peak debt. Therefore it does NOT prove that the backtest captures a debt event created by a transaction.

Replace or extend the test so the causal chain is real:

1. construct a deterministic synthetic V2-C scenario;
2. start from a state with known buying power;
3. execute an actual transaction/fill that creates a known positive margin debt;
4. ensure the debt is created by the transaction itself, not by pre-seeding the final debt state;
5. sample peak margin debt after that transaction at the relevant timestamp;
6. assert `result.peak_margin_debt` is equal to or greater than the known debt;
7. preferably assert the expected debt exactly when the fixture is deterministic;
8. assert the debt exists before any later repayment/liquidation step;
9. retain an explicit post-transaction timestamp assertion where the engine architecture permits it.

The test must exercise `run_v2_backtest()` or the actual equivalent canonical execution path that produces the reported `result.peak_margin_debt`.

A disconnected helper object that merely contains $12,000 of debt is not sufficient evidence.

### Required negative-proof property

Changing only the pre-transaction cash balance so that the transaction does NOT create debt must produce a peak debt of zero (or the correct non-debt baseline).

This proves the test is sensitive to the transaction-created debt rather than merely reading a pre-seeded portfolio field.

Do not alter production economics solely to make the fixture easier.

## 4. Final provenance model — separate execution SHA from artifact SHA

Do NOT try to make a report embed its own final Git commit SHA. That creates a self-referential provenance problem.

Use two explicit provenance fields:

- `EXECUTION_CODE_SHA`: the commit that contains the implementation actually executed for the historical run.
- `ARTIFACT_COMMIT_SHA`: the later commit that contains the final generated report/JSON and associated evidence artifacts.

Where useful, also persist:

- run ID;
- runner/config hash;
- dataset ID;
- dataset aggregate SHA;
- V2 manifest/hash;
- frozen parameter registry/hash.

### Required provenance sequence

Use this order:

1. implement the Phase L.2 code/test changes;
2. commit those code/test changes;
3. record that commit as `EXECUTION_CODE_SHA`;
4. run the frozen historical experiment using that exact commit;
5. generate the canonical JSON/Markdown from that run;
6. record the resulting artifact commit separately as `ARTIFACT_COMMIT_SHA`;
7. commit the generated artifacts;
8. do not retroactively label the artifact commit as the execution code SHA.

The report should therefore never again contain a generic ambiguous field such as only:

`Git Commit SHA:`

Replace it with unambiguous fields such as:

`Execution Code SHA`
`Artifact Commit SHA`

If the report is generated before the artifact commit exists, write the artifact field as a clearly defined placeholder only if the repository's workflow permits it; otherwise add the artifact SHA in a final artifact-only commit. The final checked-in report must contain both exact SHAs.

The JSON must contain the same provenance fields and values as the Markdown.

## 5. Accounting tolerance — make the meaning explicit

The final Phase L.1 report currently shows:

`Reconciliation Discrepancy: $0.000200`

while describing the invariant as clean.

Do not call this "machine precision" or "zero" unless the underlying unrounded values actually reconcile to zero at machine precision.

Choose one defensible approach and document it consistently:

### Preferred

Use unrounded internal values for the reconciliation algebra and only round for presentation. Then the algebraic discrepancy should be effectively zero within floating-point behavior.

### Acceptable alternative

If a non-zero residual remains because of deterministic floating-point aggregation:

- define an explicit `ACCOUNTING_TOLERANCE`;
- expose the tolerance in the result/report/JSON;
- assert `abs(reconciliation_discrepancy) <= ACCOUNTING_TOLERANCE`;
- phrase the result as `Clean within declared tolerance`, not `machine precision` or `exactly zero`.

Do not loosen the tolerance merely to make the result pass. Choose the smallest reasonable deterministic tolerance consistent with the implementation's numeric representation.

Add or update a regression test covering the declared tolerance boundary.

## 6. Final report semantics

Update the canonical report/JSON so that:

- execution SHA and artifact SHA are distinct;
- accounting tolerance is explicit;
- reconciliation status is defined against that tolerance;
- no prose claims contradict the machine-readable artifact;
- the exact Phase L and Phase L.1 preserved metrics remain distinguishable from the final Phase L.2 reproduced result;
- no prior result is silently rewritten.

If a new frozen rerun produces exactly the same ending equity as Phase L.1, state that it is a provenance/reproducibility rerun, not a strategy improvement.

If the corrected report differs numerically, explain only the mechanically necessary reason and preserve the prior artifact.

## 7. Phase L preservation-note erratum

Create:

`reports/fidelity_runs/phase_l_baseline_0ce2208/PHASE_L_PRESERVATION_NOTE_ERRATA.md`

Use the preserved canonical Phase L report/JSON as authority.

The erratum should explicitly state that the original preservation note contains stale metadata and that the archived Phase L run itself is unchanged.

At minimum document:

- original preserved SHA: `0ce2208`;
- Phase L run ID: `bc19e12e`;
- stale tactical realized P&L in the note vs actual preserved value;
- stale slippage figure in the note vs actual preserved value;
- stale closed-reference figure in the note vs actual preserved value;
- which artifact is authoritative for each corrected figure.

Do not alter `PHASE_L_PRESERVATION_NOTE.md`.

## 8. Required reproducibility rerun

After the implementation/test fixes are committed:

Run the exact frozen V2 historical experiment with:

- MU/SNDK/SKHY only;
- the same effective common start;
- the same 60% normalized core;
- the same directional parameters;
- the same tactical sizing;
- the same cost configuration;
- the same margin configuration;
- the same dataset and aggregate hash;
- the same July–September 2026 period;
- `POST_HOC_HOLDOUT / NOT_PRISTINE_OOS`.

No parameter selection or search is allowed.

The purpose of this rerun is provenance/reproducibility only.

## 9. Verification commands

Run at minimum:

`.un.ps1 test`

`.un.ps1 doctor`

`.un.ps1 doctor-data -Config configs/historical_1m.yaml -DataDir data/processed`

`..\.venv\Scripts\python.exe -m ruff check .` if needed for the repository's actual environment, otherwise use the repository's documented command.

Then run the frozen V2 historical command:

`.un.ps1 fidelity-v2-historical`

The run must be reproducible under the committed execution code SHA.

## 10. Acceptance criteria

Phase L.2 passes only if all are true:

- [ ] Phase K artifacts remain preserved.
- [ ] Phase L artifacts remain preserved.
- [ ] Phase L.1 artifacts remain distinguishable/preserved.
- [ ] Phase L preservation note is not overwritten.
- [ ] A Phase L preservation-note erratum correctly identifies and reconciles stale metadata.
- [ ] The peak-margin test creates debt through an actual transaction/execution path.
- [ ] The reported `result.peak_margin_debt` captures that transaction-created debt.
- [ ] The same fixture without debt does not falsely report positive peak debt.
- [ ] Execution code SHA is explicitly recorded.
- [ ] Artifact commit SHA is explicitly recorded.
- [ ] The provenance fields are consistent between Markdown and JSON.
- [ ] Reconciliation tolerance is explicitly defined and tested.
- [ ] Report wording matches the actual tolerance result.
- [ ] Full pytest/test command passes.
- [ ] Ruff passes.
- [ ] The frozen historical rerun, if required, is deterministic.
- [ ] No signal parameter changed.
- [ ] No universe, sizing, or cost assumption changed.
- [ ] Global research statuses remain unchanged.

Global status must remain:

`FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED`

`TRUE_LEVEL2_REPLICATION = UNVALIDATED`

`HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED`

`DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2`

`PRISTINE_OOS = UNAVAILABLE`

## 11. Required Gemini completion report

Return exactly:

1. Phase L.1 execution code SHA preserved.
2. Phase L.2 execution code SHA.
3. Phase L.2 artifact commit SHA.
4. Phase L run ID preserved.
5. Phase L.2 reproduced run ID, if rerun.
6. Exact peak-margin test fixture and causal transaction sequence.
7. Actual expected debt and reported `peak_margin_debt`.
8. Negative-control result showing no debt when the debt-creating transaction is removed or made cash-funded.
9. Exact accounting tolerance and observed discrepancy.
10. Exact Markdown/JSON provenance fields.
11. Phase L preservation-note erratum path.
12. Tests passed and lint result.
13. Confirmation that no strategy parameter, universe, sizing, cost, or margin assumption changed.
14. Remaining research blockers.

Do not claim "machine precision", "exactly zero", or "proves historical margin usage" unless the artifacts actually support that wording.

## 12. Stop condition

When all acceptance criteria pass:

STOP SOFTWARE CHANGES.

Do not proceed to parameter sweeps, strategy optimization, covered calls, Level-2 reconstruction, leveraged-product selection, or robustness research.

The next step is a separately approved research-analysis phase.
