# Gemini Execution Plan — Phase L.2.1 Final Provenance Taxonomy & Accounting-Tolerance Test Fix

## Objective

Close the two remaining review defects from Phase L.2 without changing the V2 strategy, historical economics, dataset, or frozen configuration.

Phase L.2.1 is the final test/provenance cleanup before the separately approved research-analysis phase.

This is NOT:

- a strategy change;
- a parameter search;
- a performance optimization;
- a robustness search;
- a universe change;
- a cost-model change;
- a historical experiment redesign.

## Remaining defects being fixed

### Defect 1 — Provenance field is semantically ambiguous

The final checked-in report currently contains:

`Artifact Commit SHA: d617f53`

The actual commit sequence is:

1. `c10f91c` — Phase L.2 implementation/test commit.
2. `d617f53` — generated/published the historical report and JSON while the artifact field was still a temporary `PENDING_CHECKIN` value.
3. `aaa10b5` — finalized those same report/JSON artifacts by replacing `PENDING_CHECKIN` with `d617f53`.

Therefore `d617f53` is the **artifact-content commit**, not the final provenance-finalization commit.

Do not label `d617f53` as the only generic "Artifact Commit SHA".

### Defect 2 — Accounting tolerance test is not actually a boundary test

The current `test_accounting_tolerance_boundary()` proves that the real historical/synthetic discrepancy is below the tolerance, but does not prove the acceptance boundary itself.

The production rule is:

`reconciles_cleanly = discrepancy <= ACCOUNTING_TOLERANCE`

The test suite must explicitly prove:

- discrepancy below tolerance -> accepted;
- discrepancy exactly equal to tolerance -> accepted;
- discrepancy above tolerance -> rejected.

Do this without changing production economics or weakening the tolerance.

---

# 1. Hard scope rules

Do NOT:

- change any V2 directional parameter;
- change the 60% normalized core assumption;
- change MU/SNDK/SKHY;
- change tactical sizing;
- change slippage, commission, financing, maintenance, or leverage assumptions;
- change the historical dataset;
- change the effective evaluation start;
- force historical margin usage;
- change the historical run's strategy behavior;
- add covered calls;
- add Level-2;
- add KRX/Tokyo execution;
- alter Phase K, Phase L, or Phase L.1 preserved artifacts;
- perform a parameter sweep;
- reinterpret the Phase L.2 historical result.

A historical rerun is NOT required merely to rename provenance fields or strengthen a unit test. Only rerun the frozen V2 historical experiment if a code-path change to report generation makes it mechanically necessary to regenerate the canonical artifacts.

The final historical performance must remain:

- V2-A: +6.48% / $106,482.16
- V2-B: +7.93% / $107,928.85
- V2-C: +7.93% / $107,928.85
- Tactical contribution: +$1,446.69
- Historical peak margin debt: $0.00

Do not "improve" these values.

---

# 2. Read first

Read:

1. `docs/execution_plan/REDDIT_V2_PHASE_L2_FINAL_PROVENANCE_AND_MARGIN_TEST_FIX_PLAN.md`
2. `docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md`
3. `reports/V2_HISTORICAL_COMPARISON.md`
4. `reports/v2_historical_comparison.json`
5. `tests/test_v2_post_run_audit.py`
6. `src/tactical_engine/research/v2_historical_runner.py`
7. `src/tactical_engine/backtest/v2_engine.py`
8. commits `c10f91c`, `d617f53`, and `aaa10b5`.

Record the current file SHAs before editing.

---

# 3. Fix provenance taxonomy

## Required provenance fields

The final canonical report and JSON must expose these distinct fields:

`EXECUTION_CODE_SHA`

Meaning:

> The exact implementation/test commit whose code was executed for the historical run.

For the current Phase L.2 historical run this is:

`c10f91c`

---

`ARTIFACT_CONTENT_COMMIT_SHA`

Meaning:

> The commit that introduced/published the generated historical Markdown/JSON artifact content for the run.

For the current Phase L.2 historical run this is:

`d617f53`

---

`PROVENANCE_FINALIZATION_COMMIT_SHA`

Meaning:

> The later commit that finalized the artifact's embedded provenance metadata.

For the current Phase L.2 historical run this is:

`aaa10b5`

This field exists specifically because the artifact cannot safely self-reference its own final commit.

## Required implementation behavior

Update the result/report model and canonical Markdown/JSON so the terminology is explicit.

Do NOT:

- continue presenting `d617f53` as a generic "Artifact Commit SHA";
- replace it with `aaa10b5` while keeping the generic field name;
- create a fake self-referential final artifact SHA;
- remove the execution SHA.

Recommended final report header:

```text
Run ID: 24a9e783
Execution Code SHA: c10f91c
Artifact Content Commit SHA: d617f53
Provenance Finalization Commit SHA: aaa10b5
```

Recommended JSON fields:

```json
{
  "execution_code_sha": "c10f91c",
  "artifact_content_commit_sha": "d617f53",
  "provenance_finalization_commit_sha": "aaa10b5"
}
```

If backward compatibility requires `git_sha`, preserve it only as an alias of `execution_code_sha` and document that it is deprecated.

## Provenance integrity test

Add or extend a test that:

- loads the canonical JSON;
- verifies the three provenance fields exist;
- verifies they are internally consistent with the documented current Phase L.2 run;
- verifies `git_sha == execution_code_sha` if the backward-compatible alias remains.

Do not use the test to invent a different SHA.

---

# 4. Fix the accounting-tolerance test

The production rule must remain exactly:

`reconciles_cleanly = discrepancy <= ACCOUNTING_TOLERANCE`

Do not modify the tolerance value merely to pass tests.

## Required test behavior

Replace/extend `test_accounting_tolerance_boundary()` so it directly verifies the boundary logic.

At minimum, the test must establish:

### Case A — below tolerance

`discrepancy = ACCOUNTING_TOLERANCE - epsilon`

Expected:

`True`

### Case B — exactly at tolerance

`discrepancy = ACCOUNTING_TOLERANCE`

Expected:

`True`

This is the critical boundary.

### Case C — above tolerance

`discrepancy = ACCOUNTING_TOLERANCE + epsilon`

Expected:

`False`

Use a small deterministic epsilon appropriate to the numeric representation, such as `1e-9`, unless the implementation requires a different explicitly justified value.

## Test design requirement

Prefer testing the boolean decision function or the actual reconciliation status calculation directly rather than mutating unrelated portfolio economics.

If no isolated helper exists, factor out a tiny pure helper whose ONLY job is:

```python
def is_within_accounting_tolerance(discrepancy: float) -> bool:
    return discrepancy <= ACCOUNTING_TOLERANCE
```

Then unit-test the three cases.

Do NOT introduce rounding that changes the historical accounting result.

---

# 5. Preserve the historical result

The canonical historical result must remain economically unchanged.

After the L.2.1 edits, verify:

- V2-A final equity = $106,482.16
- V2-B final equity = $107,928.85
- V2-C final equity = $107,928.85
- Tactical contribution = $1,446.69
- V2-C historical peak margin debt = $0.00
- reconciliation discrepancy = $0.000200
- accounting tolerance = $0.001000

No new performance interpretation is allowed.

If report regeneration is necessary solely because the report schema changed, preserve the same Run ID `24a9e783` only if the project's provenance rules explicitly support a metadata-only regeneration; otherwise create a clearly labeled metadata-correction artifact and retain the original L.2 report unchanged.

Do not generate a new historical strategy run.

---

# 6. Verification

Run:

`.un.ps1 test`

`.un.ps1 doctor`

`.un.ps1 doctor-data -Config configs/historical_1m.yaml -DataDir data/processed`

`..\.venv\Scripts\python.exe -m ruff check .` using the repository's actual documented environment path.

Do NOT run `fidelity-v2-historical` unless required by a mechanical report-generation change.

If the historical runner/report schema is modified and a regeneration is mechanically required, use the exact same frozen dataset/config and explain why no strategy behavior changed.

---

# 7. Acceptance criteria

Phase L.2.1 passes only if ALL are true:

- [ ] No V2 strategy parameter changed.
- [ ] No universe changed.
- [ ] No sizing/cost/margin assumption changed.
- [ ] Phase K artifacts unchanged.
- [ ] Phase L artifacts unchanged.
- [ ] Phase L.1 preservation unchanged.
- [ ] Phase L preservation erratum unchanged except where strictly necessary for provenance references.
- [ ] `EXECUTION_CODE_SHA` is explicit.
- [ ] `ARTIFACT_CONTENT_COMMIT_SHA` is explicit.
- [ ] `PROVENANCE_FINALIZATION_COMMIT_SHA` is explicit.
- [ ] No ambiguous generic artifact SHA remains.
- [ ] `git_sha`, if retained, equals `execution_code_sha`.
- [ ] Canonical JSON and Markdown agree on provenance.
- [ ] Tolerance-below case passes.
- [ ] Tolerance-exact-boundary case passes.
- [ ] Tolerance-above-boundary case passes.
- [ ] Full test suite passes.
- [ ] Ruff passes.
- [ ] Doctor passes.
- [ ] Doctor-data passes.
- [ ] Historical economics remain unchanged.
- [ ] Global epistemic statuses remain unchanged.

Global status must remain:

`FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED`

`TRUE_LEVEL2_REPLICATION = UNVALIDATED`

`HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED`

`DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2`

`PRISTINE_OOS = UNAVAILABLE`

---

# 8. Required Gemini completion report

Return exactly:

1. files changed;
2. previous provenance fields;
3. final provenance fields;
4. exact commit meanings for all three SHAs;
5. tolerance test design;
6. below/equal/above boundary results;
7. full test count;
8. Ruff result;
9. doctor result;
10. doctor-data result;
11. confirmation that no historical strategy run was changed or rerun unnecessarily;
12. confirmation that V2-A/B/C historical economics remain unchanged;
13. remaining research blockers.

Do not report this phase as strategy validation.

---

# 9. Final stop condition

When all acceptance criteria pass:

**STOP SOFTWARE CHANGES.**

Do not continue to another engineering phase.

The next step is a separately approved research-analysis phase.
