# Reddit V2 Phase M.1.2 — Provenance Seal and Remote Synchronization Plan

**Status:** REQUIRED FINALIZATION REPAIR  
**Phase:** M.1.2  
**Reason:** Phase M.1.1 local implementation reports success, but its final commit is not present on the GitHub remote and the provenance field has a self-reference/semantic-finalization problem.

---

## 1. Audit Finding

The Phase M.1.1 completion report states:

- `EXECUTION_CODE_SHA = 30473ee`
- `ARTIFACT_CONTENT_COMMIT_SHA = c691672`
- `PROVENANCE_FINALIZATION_COMMIT_SHA = 81d9649`
- final local commit = `e84e681`

However, repository verification shows that GitHub currently does **not** resolve `e84e681` as a remote commit.

Therefore Phase M.1.1 is not yet remotely synchronized/accepted.

More importantly, commit `81d9649` was the original M.1 commit whose own artifact content still recorded:

`PROVENANCE_FINALIZATION_COMMIT_SHA = UNAVAILABLE`

A commit cannot retroactively contain its own final SHA. Therefore `81d9649` cannot truthfully be described as the final provenance value for the artifact that was subsequently modified by M.1.1.

The correct repair is to explicitly distinguish:

1. the original execution code commit;
2. the original Phase M artifact-content commit;
3. the M.1 audit/provenance implementation commit;
4. the final local sealing/recording commit;
5. the remote synchronization state.

Do not improvise another ambiguous SHA meaning.

---

# 2. Non-Negotiable Preservation Rules

Do not:

- rerun `bb0887e4` performance;
- alter its economic results;
- change any strategy parameter;
- change the historical Run `24a9e783`;
- change the OOS dataset;
- alter continuation logic except to correct provenance/schema semantics;
- regenerate the two-session backtest.

This is a provenance/repository-state repair only.

The existing observed result remains:

- V2-A +1.21%;
- V2-B +0.92%;
- V2-C +0.92%;
- tactical contribution -$290.98;
- 2 complete sessions;
- `PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE`;
- `NEUTRAL / INCONCLUSIVE`.

---

# 3. First Task — Verify Local Commit Ancestry

On the Gemini machine, inspect:

`git show -s --format=fuller 30473ee`

`git show -s --format=fuller c691672`

`git show -s --format=fuller 81d9649`

`git show -s --format=fuller e84e681`

`git log --graph --decorate --oneline --max-count=20`

`git status --short`

Establish the exact parent/child relationship.

Do not rely on the previous completion report alone.

---

# 4. Provenance Semantics

Use these meanings permanently.

## 4.1 EXECUTION_CODE_SHA

The exact commit containing the strategy/execution code and frozen configuration at the moment before prospective data acquisition/evaluation.

For Phase M this remains:

`30473ee`

This value must never move because of later audit commits.

---

## 4.2 ARTIFACT_CONTENT_COMMIT_SHA

The original commit that first persisted the actual Phase M performance artifact/dataset manifest.

For Phase M this remains:

`c691672`

This is the historical provenance of the original observed result.

Do not replace this with an audit/reformat commit.

---

## 4.3 PROVENANCE_FINALIZATION_COMMIT_SHA

This field must **not** be self-referential.

A commit cannot reliably contain its own SHA before it exists.

Therefore the repository must use a two-step sealing convention:

### Commit A

A commit contains:

- all corrected artifact/report/provenance content;
- all intended provenance fields except that the finalization SHA may temporarily be `UNAVAILABLE` if necessary.

### Commit B

A subsequent commit records the SHA of Commit A as:

`PROVENANCE_FINALIZATION_COMMIT_SHA = <Commit A SHA>`

Commit B becomes the final published artifact state.

This makes the provenance claim mechanically verifiable without self-reference.

### Required final semantics

The final published artifact should therefore show:

`EXECUTION_CODE_SHA = 30473ee`

`ARTIFACT_CONTENT_COMMIT_SHA = c691672`

`PROVENANCE_FINALIZATION_COMMIT_SHA = <SHA of the immediately preceding corrected provenance commit>`

The exact SHA must be derived from Git history, never guessed.

---

# 5. Reconcile the Existing M.1.1 Commit

The currently reported local commit `e84e681` appears to contain the M.1.1 repairs.

Before doing anything else:

1. verify its full 40-character SHA;
2. verify that it is descended from `81d9649`;
3. inspect its diff;
4. confirm that no strategy-calculation files outside the approved M.1.1 scope changed unexpectedly;
5. verify economic artifacts remain unchanged.

If `e84e681` is the corrected implementation/artifact commit, use its full SHA as **Commit A** in the two-step sealing process.

Do not claim `81d9649` is the final provenance SHA if the final artifact content was actually changed afterward.

---

# 6. Create a Final Provenance-Sealing Commit

Create a small, isolated follow-up commit after the corrected M.1.1 commit.

Its only purpose is to finalize/report the verified provenance of the corrected M.1.1 artifacts.

Update:

- `reports/v2_oos/bb0887e4.md`;
- `reports/v2_oos/bb0887e4.json`;
- `reports/fidelity_runs/v2_oos_bb0887e4/bb0887e4.md`;
- `reports/fidelity_runs/v2_oos_bb0887e4/bb0887e4.json`;
- `reports/fidelity_runs/v2_oos_bb0887e4/PRESERVATION_NOTE.md`;

only as required to make the provenance taxonomy internally consistent.

The finalization commit must not change:

- P&L;
- equity curves;
- trade records;
- session count;
- data hashes;
- strategy parameters;
- configuration hashes.

Do not touch the historical control artifacts.

---

# 7. Verify SHA Non-Equality

The final report should satisfy:

`EXECUTION_CODE_SHA != ARTIFACT_CONTENT_COMMIT_SHA`

and, where the actual history requires a separate sealing commit:

`ARTIFACT_CONTENT_COMMIT_SHA != PROVENANCE_FINALIZATION_COMMIT_SHA`

Add a regression test preventing accidental reuse/collapse of these roles.

Do **not** enforce arbitrary pairwise SHA inequality merely for appearance if repository history legitimately makes two roles identical. The test should enforce semantic correctness against the established expected lineage.

---

# 8. Remote Synchronization Gate

The final sealing commit must be pushed to:

`origin/main`

Then verify remotely.

Required commands:

`git push origin main`

`git status --short`

`git rev-parse HEAD`

Then verify through the GitHub repository that:

- the final sealing commit exists remotely;
- `origin/main` points to that commit;
- the M.1.1 implementation commit is an ancestor;
- all intended reports/tests are visible remotely.

Do not declare Phase M.1.1 complete while the final implementation exists only locally.

---

# 9. Completion Report Must Distinguish Local vs Remote State

The final Gemini completion report must contain:

### Local

`LOCAL_FINAL_HEAD_SHA = ...`

### Remote

`REMOTE_ORIGIN_MAIN_SHA = ...`

These must be equal before acceptance.

Also report:

`EXECUTION_CODE_SHA = 30473ee`

`ARTIFACT_CONTENT_COMMIT_SHA = c691672`

`PROVENANCE_FINALIZATION_COMMIT_SHA = ...`

with one-line semantic definitions.

---

# 10. Verify M.1.1 Functional Repairs Were Not Lost

Re-run verification only.

Do not run performance.

Required:

`..venvScriptspython.exe -m pytest -v tests/test_v2_oos_validation.py`

`..venvScriptspython.exe -m pytest`

`..venvScriptspython.exe -m ruff check .`

`powershell -ExecutionPolicy Bypass -File .\run.ps1 test`

`powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor`

`powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor-data -DataDir data/processed_oos -Config configs/v2_oos_frozen.yaml`

`git status --short`

The OOS data-doctor must explicitly target:

`data/processed_oos`

with:

`configs/v2_oos_frozen.yaml`

Do not substitute the default historical doctor.

---

# 11. Verify Continuation Tests Remain Present

The completed M.1.1 test suite reported 25 targeted tests / 180 full tests.

Confirm the following remain:

- CLI continuation arguments;
- paired lineage validation;
- initial 2026-10-01 freeze;
- forward continuation acceptance;
- overlap rejection;
- historical cutoff enforcement;
- new-run-ID protection;
- lineage serialization;
- provenance taxonomy;
- frozen strategy fingerprint.

No test should invoke a real performance run as part of this verification.

---

# 12. Artifact Integrity Check

Before acceptance, compare the economic payload in the final artifacts against the original `bb0887e4` observation.

Must remain exactly:

`V2-A = +1.21%`

`V2-B = +0.92%`

`V2-C = +0.92%`

`Tactical contribution = -$290.98`

`Sessions = 2`

`Peak margin debt = $0.00`

`Interpretation = NEUTRAL / INCONCLUSIVE`

The dataset ID/hash must remain:

`massive_stocks_1m_c857b18f710f`

`c857b18f710fb7f59e82ecdb6816c8524914c8a003e70912196c86ba2edfcac2`

Any difference requires escalation rather than silent correction.

---

# 13. Historical Control Protection

Verify that:

`reports/v2_historical_comparison.json`

and:

`reports/V2_HISTORICAL_COMPARISON.md`

remain byte-identical to the accepted Run 24a9e783 state.

Do not regenerate them.

---

# 14. No Scientific Reinterpretation

Do not change:

`PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE`

or:

`NEUTRAL / INCONCLUSIVE`

The first two sessions remain monitoring observations, not validation.

---

# 15. Required Final Report

The completion report must include:

### A. Git lineage

- full SHA for 30473ee;
- full SHA for c691672;
- full SHA for M.1.1 corrected implementation commit;
- full SHA for final sealing commit.

### B. Provenance schema

Explain exactly what each SHA means.

### C. Remote synchronization

State:

- local HEAD;
- origin/main;
- equality check.

### D. Verification

Report exact numerical results for:

- targeted pytest;
- full pytest;
- Ruff;
- canonical test;
- doctor;
- OOS doctor-data.

### E. Preservation

Explicitly state:

`NO PERFORMANCE RERUN OF bb0887e4 PERFORMED`

and confirm all economic invariants.

### F. Scientific state

`PRISTINE_OOS = PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE`

`INTERPRETATION_CLASS = NEUTRAL / INCONCLUSIVE`

`FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED`

---

# 16. Acceptance Criteria

M.1.2 is accepted only if all conditions are true:

- [ ] M.1.1 corrected implementation commit exists locally.
- [ ] M.1.1 corrected implementation commit exists remotely.
- [ ] Final sealing commit exists locally.
- [ ] Final sealing commit exists remotely.
- [ ] local HEAD == origin/main.
- [ ] provenance roles are semantically distinct and Git-verifiable.
- [ ] no self-referential SHA claim exists.
- [ ] no active generic `artifact_commit_sha`.
- [ ] OOS-targeted doctor-data passes.
- [ ] full tests pass.
- [ ] targeted tests pass.
- [ ] Ruff passes.
- [ ] canonical test passes.
- [ ] doctor passes.
- [ ] working tree is clean.
- [ ] `bb0887e4` was not rerun.
- [ ] economic results are unchanged.
- [ ] historical control remains untouched.
- [ ] scientific interpretation remains NEUTRAL / INCONCLUSIVE.

---

# 17. Final Stop State

After this package is accepted:

**STOP SOFTWARE CHANGES.**

The Phase M infrastructure/audit layer is then considered frozen.

Future work may only be:

- collecting genuinely new chronological OOS sessions;
- executing the already-approved Phase N options track;
- executing the already-approved Phase O Level-2 track.

No tuning from the two-session result.
