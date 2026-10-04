# Gemini Execution Plan — Phase L.2.1.1 Final Artifact Schema Cleanup

## 0. Purpose

This is the final, surgical follow-up to Phase L.2.1.

The previous L.2.1 implementation successfully completed the accounting-tolerance boundary tests and added the three intended provenance concepts, but it retained one deprecated field:

`artifact_commit_sha`

That field is still semantically ambiguous and directly violates the L.2.1 acceptance criterion:

> No ambiguous generic artifact SHA remains.

Phase L.2.1.1 exists ONLY to remove that remaining schema ambiguity and prove that the canonical report/JSON and tests use the explicit three-field provenance model.

This is not a research experiment.

This is not a backtest correction.

This is not a strategy modification.

This phase should be treated as a documentation/schema/test cleanup with zero economic impact.

---

# 1. HARD STOP RULES

Do NOT:

- change any V2 signal parameter;
- change the normalized 60% core assumption;
- change MU/SNDK/SKHY;
- change tactical sizing;
- change slippage assumptions;
- change commission assumptions;
- change financing assumptions;
- change maintenance ratio;
- change leverage assumptions;
- change the historical dataset;
- change the effective evaluation start;
- change the historical run ID;
- rerun `fidelity-v2-historical`;
- regenerate the historical strategy result;
- perform any parameter search;
- perform any robustness search;
- add options;
- add Level-2;
- add KRX/Tokyo execution;
- modify Phase K preserved artifacts;
- modify Phase L preserved artifacts;
- modify Phase L.1 preserved artifacts;
- modify the preserved Phase L preservation note;
- modify the Phase L preservation-note erratum;
- modify historical P&L numbers.

### Critical interpretation

The historical run is already accepted as the Phase L.2 reproduced result:

`Run ID = 24a9e783`

The implementation used for that historical run remains:

`EXECUTION_CODE_SHA = c10f91c`

Do not rerun the strategy just to prove this cleanup.

This phase changes schema semantics only.

---

# 2. READ FIRST

Read these exact files before editing:

1. `docs/execution_plan/REDDIT_V2_PHASE_L2_1_FINAL_PROVENANCE_TAXONOMY_AND_TOLERANCE_TEST_PLAN.md`
2. `docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md`
3. `src/tactical_engine/research/v2_historical_runner.py`
4. `reports/V2_HISTORICAL_COMPARISON.md`
5. `reports/v2_historical_comparison.json`
6. `tests/test_v2_post_run_audit.py`
7. the latest commit implementing L.2.1, currently:
   `97fd7dc`

Before editing, record:

- current HEAD SHA;
- current SHA of each of the four files above that will be modified;
- current values of the three explicit provenance fields;
- current presence/value of the deprecated aliases.

Do not assume the repository is clean until `git status` confirms it.

---

# 3. CURRENT STATE — WHAT IS WRONG

The canonical model currently contains:

```python
execution_code_sha: str = ""
artifact_content_commit_sha: str = ""
provenance_finalization_commit_sha: str = ""
artifact_commit_sha: str = ""  # deprecated alias of artifact_content_commit_sha
git_sha: str = ""  # deprecated alias of execution_code_sha
```

The canonical JSON therefore still contains both:

```json
"execution_code_sha": "c10f91c",
"artifact_content_commit_sha": "d617f53",
"provenance_finalization_commit_sha": "aaa10b5",
"artifact_commit_sha": "d617f53",
"git_sha": "c10f91c"
```

The Markdown header already contains the correct explicit three-field taxonomy:

```text
Execution Code SHA: c10f91c
Artifact Content Commit SHA: d617f53
Provenance Finalization Commit SHA: aaa10b5
```

### The defect

`artifact_commit_sha` remains in the model/JSON.

It is ambiguous because its name does not tell the reader whether it means:

- the commit that first published the artifact;
- the commit that finalized the artifact;
- the commit used to execute the code;
- or the final repository state.

The explicit fields already solve this problem.

Therefore:

## REMOVE `artifact_commit_sha` entirely.

Do NOT merely mark it deprecated.

Do NOT keep it as an alias.

Do NOT add another generic artifact field.

---

# 4. REQUIRED FINAL PROVENANCE CONTRACT

After this phase, the canonical result model MUST expose exactly these provenance fields as first-class fields:

### Field 1

`execution_code_sha`

Definition:

> Exact implementation/test commit whose code was executed for the historical run.

Required current value:

`c10f91c`

### Field 2

`artifact_content_commit_sha`

Definition:

> Commit that published the generated historical Markdown/JSON artifact content.

Required current value:

`d617f53`

### Field 3

`provenance_finalization_commit_sha`

Definition:

> Later commit that finalized the embedded provenance metadata.

Required current value:

`aaa10b5`

### Backward-compatible alias

`git_sha`

This may remain ONLY because the prior schema used it and its meaning is unambiguous enough when explicitly documented as:

> Deprecated compatibility alias of `execution_code_sha`.

Its value MUST equal:

`c10f91c`

### Forbidden field

`artifact_commit_sha`

This field MUST NOT exist in:

- the Pydantic result model;
- generated JSON;
- generated Markdown;
- report-generation code;
- tests;
- documentation describing the final schema.

Do not use a compatibility alias for this field.

---

# 5. EXACT CODE CHANGES

## 5A. `src/tactical_engine/research/v2_historical_runner.py`

Locate the `V2HistoricalComparisonResult` model.

### BEFORE

It currently contains conceptually:

```python
execution_code_sha: str = ""
artifact_content_commit_sha: str = ""
provenance_finalization_commit_sha: str = ""
artifact_commit_sha: str = ""
git_sha: str = ""
```

### REQUIRED AFTER

It must contain:

```python
execution_code_sha: str = ""
artifact_content_commit_sha: str = ""
provenance_finalization_commit_sha: str = ""
git_sha: str = ""  # deprecated compatibility alias of execution_code_sha
```

Delete the `artifact_commit_sha` field.

Search the ENTIRE file for the literal:

`artifact_commit_sha`

After the edit, there must be ZERO occurrences.

Do not merely stop rendering it; remove it from the model and all code paths.

---

# 5B. Search the entire repository

Run a repository-wide search for:

`artifact_commit_sha`

Use the repository's normal search command.

The desired final result is:

> ZERO production-code, report-generation, test, and current-document references.

There may be an old historical text inside a preserved artifact or historical commit diff, but do NOT modify preserved historical artifacts solely to erase historical evidence.

Distinguish:

### Must be removed

- current `src/` production code;
- current `tests/` code;
- current canonical `reports/V2_HISTORICAL_COMPARISON.md`;
- current canonical `reports/v2_historical_comparison.json`;
- current active execution plans documenting the final schema;
- current completion/handoff documentation if it describes the final schema.

### Must NOT be modified solely for this cleanup

- immutable Phase K artifacts;
- immutable Phase L artifacts;
- immutable Phase L.1 artifacts;
- archived historical completion reports whose role is to preserve what previously happened.

If an archived historical document contains the old name as historical evidence, leave it alone unless the file is explicitly an active specification.

---

# 6. EXACT CURRENT JSON CONTRACT

The current canonical JSON must end up with:

```json
{
  "run_id": "24a9e783",
  "execution_code_sha": "c10f91c",
  "artifact_content_commit_sha": "d617f53",
  "provenance_finalization_commit_sha": "aaa10b5",
  "git_sha": "c10f91c"
}
```

The exact JSON contains many more fields; this snippet defines only the provenance subset.

It MUST NOT contain:

```json
"artifact_commit_sha": "d617f53"
```

Do not change any other historical metrics.

---

# 7. EXACT CURRENT MARKDOWN CONTRACT

The canonical report header must contain:

```text
**Execution Code SHA:** `c10f91c`
**Artifact Content Commit SHA:** `d617f53`
**Provenance Finalization Commit SHA:** `aaa10b5`
```

It must NOT contain any line of the form:

```text
Artifact Commit SHA:
Git Commit SHA:
```

unless the latter is being discussed explicitly as a historical/backward-compatibility note outside the canonical provenance header.

Do not change:

- Run ID;
- dataset ID;
- dataset hash;
- effective evaluation start;
- final equity;
- returns;
- tactical P&L;
- trade counts;
- margin metrics;
- tolerance;
- epistemic statuses.

---

# 8. CLI / RUNNER COMPATIBILITY

Inspect the runner's CLI arguments and any report-generation call sites.

The explicit fields must continue to be accepted and emitted:

- `execution_code_sha`
- `artifact_content_commit_sha`
- `provenance_finalization_commit_sha`

If the runner currently accepts `artifact_commit_sha` as an argument, REMOVE that argument.

Do NOT keep a hidden compatibility input for `artifact_commit_sha`.

The goal is to make misuse impossible in the active code path.

The `git_sha` compatibility alias may remain only if already part of the existing public result/JSON contract. If retained, make sure its value is derived from `execution_code_sha`, not independently supplied with a potentially conflicting value.

---

# 9. TEST REQUIREMENTS

## 9A. Existing canonical report test

Update:

`tests/test_v2_post_run_audit.py`

The test that verifies Markdown/JSON consistency must explicitly assert:

```python
data["execution_code_sha"] == "c10f91c"
data["artifact_content_commit_sha"] == "d617f53"
data["provenance_finalization_commit_sha"] == "aaa10b5"
data["git_sha"] == data["execution_code_sha"]
```

And also explicitly assert:

```python
"artifact_commit_sha" not in data
```

The test should also inspect the Markdown text and verify:

- `Artifact Content Commit SHA: d617f53` is present;
- `Provenance Finalization Commit SHA: aaa10b5` is present;
- generic `Artifact Commit SHA:` is absent from the canonical report header.

Do not test merely that the new fields exist. Test that the ambiguous field is absent.

---

## 9B. Model-level serialization test

Add a focused assertion that creating/serializing `V2HistoricalComparisonResult` does not produce:

`artifact_commit_sha`

If the model is already exercised by the canonical report test, you may avoid a redundant test, but the acceptance criterion must be directly covered.

---

## 9C. Backward-compatible `git_sha`

If `git_sha` is retained, assert:

```python
data["git_sha"] == data["execution_code_sha"]
```

Do not create a second source of truth.

---

# 10. DO NOT MODIFY TOLERANCE LOGIC

The following must remain unchanged:

```python
ACCOUNTING_TOLERANCE = 0.001
```

and:

```python
def is_within_accounting_tolerance(discrepancy: float) -> bool:
    return discrepancy <= ACCOUNTING_TOLERANCE
```

The below/equal/above tolerance tests are already complete.

Do NOT touch them except if required for unrelated import/test hygiene.

---

# 11. PRESERVE HISTORICAL NUMBERS EXACTLY

Before and after the cleanup, assert these values remain unchanged in the canonical JSON:

```text
run_id                         = 24a9e783
execution_code_sha             = c10f91c
artifact_content_commit_sha    = d617f53
provenance_finalization_commit_sha = aaa10b5
git_sha                        = c10f91c

V2-A final_equity              = 106482.16
V2-B final_equity              = 107928.85
V2-C final_equity              = 107928.85

V2-A total_return_pct          = +6.48%
V2-B total_return_pct          = +7.93%
V2-C total_return_pct          = +7.93%

tactical net contribution      = +1446.69
peak historical V2-C debt      = 0.00

reconciliation discrepancy     = 0.000200
accounting tolerance           = 0.001000

completed round trips          = 108
open tactical lots             = 6
open tactical shares           = 79
```

If any of these values change, STOP and report the change.

Do not "fix" a changed value by hand.

The expected outcome is that none of them changes.

---

# 12. NO HISTORICAL RERUN

Do NOT run:

```powershell
.un.ps1 fidelity-v2-historical
```

The only reason this command would become permissible is if removing `artifact_commit_sha` forces a full artifact regeneration through a code path that cannot be updated safely without execution.

That is NOT expected.

Prefer updating the existing canonical JSON/Markdown metadata in place while preserving the exact Run ID and historical values.

This is a metadata/schema cleanup, not a new run.

---

# 13. VERIFICATION COMMANDS

Run, in order:

### Step 1 — repository status

```powershell
git status
```

Expected before editing:

- only pre-existing intended work, if any;
- do not overwrite unrelated user changes.

### Step 2 — targeted test

```powershell
.\.venv\Scripts\python.exe -m pytest -v tests/test_v2_post_run_audit.py
```

Expected:

> all tests pass.

### Step 3 — full suite

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1 test
```

Expected:

> 154 passed

or a larger count only if an additional test was intentionally added. Report the exact count.

### Step 4 — lint

```powershell
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

> All checks passed.

### Step 5 — doctor

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor
```

Expected:

> all checks passed.

### Step 6 — data doctor

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor-data -Config configs/historical_1m.yaml -DataDir data/processed
```

Expected:

> all required symbols present and valid.

### Step 7 — repository-wide search

Search for:

`artifact_commit_sha`

The active repository should return ZERO matches in:

- `src/`
- `tests/`
- `reports/V2_HISTORICAL_COMPARISON.md`
- `reports/v2_historical_comparison.json`

Also search for the exact Markdown label:

`Artifact Commit SHA:`

The active canonical report must return ZERO matches.

If archived historical evidence contains the old wording, that is acceptable ONLY when it is truly historical and not an active specification.

---

# 14. DIFF REVIEW BEFORE COMMIT

Run:

```powershell
git diff --check
git diff -- src/tactical_engine/research/v2_historical_runner.py tests/test_v2_post_run_audit.py reports/V2_HISTORICAL_COMPARISON.md reports/v2_historical_comparison.json
```

The intended diff should be narrow:

### Expected production change

- remove `artifact_commit_sha` from the result model;
- remove any active CLI/report-generation references to it.

### Expected test change

- assert `artifact_commit_sha` is absent;
- verify the three explicit SHAs;
- verify `git_sha` aliases execution SHA if retained.

### Expected report change

- remove the deprecated `artifact_commit_sha` JSON field;
- leave the three explicit SHA fields unchanged;
- leave all economics unchanged.

### Forbidden diff

Any change to:

- signal logic;
- portfolio sizing;
- execution costs;
- margin behavior;
- dataset;
- historical trade records;
- P&L;
- returns;
- drawdown;
- run ID.

If such a change appears, STOP.

---

# 15. COMMIT DISCIPLINE

Create exactly one focused commit for this phase, for example:

```text
fix(audit): remove ambiguous artifact commit provenance alias
```

Push that commit to `origin/main`.

Do NOT squash historical commits.

Do NOT amend `c10f91c`, `d617f53`, or `aaa10b5`.

Those commits are evidence and must remain immutable.

---

# 16. FINAL ACCEPTANCE CHECKLIST

Phase L.2.1.1 passes ONLY when ALL are true:

- [ ] `artifact_commit_sha` removed from the active result model.
- [ ] `artifact_commit_sha` removed from active JSON serialization.
- [ ] `artifact_commit_sha` removed from active report generation.
- [ ] `artifact_commit_sha` removed from active tests.
- [ ] canonical JSON contains exactly the three explicit provenance fields plus optional `git_sha` compatibility alias.
- [ ] `execution_code_sha == c10f91c`.
- [ ] `artifact_content_commit_sha == d617f53`.
- [ ] `provenance_finalization_commit_sha == aaa10b5`.
- [ ] if present, `git_sha == execution_code_sha`.
- [ ] canonical Markdown contains the three explicit provenance labels.
- [ ] canonical Markdown does not use generic `Artifact Commit SHA:`.
- [ ] tolerance logic remains unchanged.
- [ ] below/equal/above tolerance tests remain passing.
- [ ] full test suite passes.
- [ ] Ruff passes.
- [ ] doctor passes.
- [ ] doctor-data passes.
- [ ] no historical rerun occurred.
- [ ] historical Run ID remains `24a9e783`.
- [ ] all historical economics remain identical.
- [ ] preserved Phase K/L/L.1 artifacts remain untouched.
- [ ] global epistemic statuses remain unchanged.

Global status must remain:

```text
FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED
TRUE_LEVEL2_REPLICATION = UNVALIDATED
HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED
DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2
PRISTINE_OOS = UNAVAILABLE
```

---

# 17. REQUIRED GEMINI COMPLETION REPORT

Return exactly these sections:

## A. Scope

State explicitly:

> Metadata/schema/test cleanup only. No strategy or historical rerun.

## B. Files changed

List every modified file and what changed.

## C. Provenance contract

Report:

```text
EXECUTION_CODE_SHA = c10f91c
ARTIFACT_CONTENT_COMMIT_SHA = d617f53
PROVENANCE_FINALIZATION_COMMIT_SHA = aaa10b5
git_sha alias = c10f91c   # only if retained
artifact_commit_sha = ABSENT
```

## D. Search proof

Report the result of repository-wide searches for:

- `artifact_commit_sha`
- `Artifact Commit SHA:`

Distinguish active-code/report matches from archived historical evidence.

## E. Test proof

Report:

- targeted test result;
- full test count;
- Ruff;
- doctor;
- doctor-data.

## F. Historical invariance proof

Report unchanged:

- Run ID;
- V2-A/B/C ending equity;
- returns;
- tactical contribution;
- round trips;
- open lots/shares;
- historical peak margin debt;
- discrepancy;
- tolerance.

## G. Commit

Report the new commit SHA and push status.

## H. Final blocker status

State that the only remaining blockers are research-validity blockers:

- historical option-chain validation;
- genuine Level-2 validation;
- direct Asia execution scope;
- pristine OOS unavailability.

Do not invent any new engineering blocker.

---

# 18. FINAL STOP CONDITION

When the acceptance checklist passes:

# STOP SOFTWARE CHANGES

Do not create another engineering phase for this provenance issue.

Do not rerun the historical strategy.

Do not tune parameters.

Do not expand scope.

The repository is then frozen for the separately approved research-analysis phase.

The next task is to interpret the evidence and decide whether a genuinely unseen OOS experiment can be constructed.
