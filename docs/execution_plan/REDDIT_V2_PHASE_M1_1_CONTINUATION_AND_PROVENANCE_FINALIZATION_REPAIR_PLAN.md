# Reddit V2 Phase M.1.1 — Continuation Wiring, Provenance Finalization, and Data-Doctor Repair

**Status:** REQUIRED REPAIR — M.1 NOT YET ACCEPTED  
**Phase:** M.1.1  
**Primary artifact:** `bb0887e4`  
**Historical control:** `24a9e783`  
**Strategy:** FROZEN  
**Performance rerun of `bb0887e4`: PROHIBITED**

---

## 1. Executive Finding

The Phase M.1 implementation substantially improved the report structure and schema, but the completion claim cannot yet be accepted.

Three concrete defects remain.

### Defect A — Provenance finalization is misclassified

The repaired artifacts now contain:

`EXECUTION_CODE_SHA = 30473ee`

`ARTIFACT_CONTENT_COMMIT_SHA = c691672`

`PROVENANCE_FINALIZATION_COMMIT_SHA = UNAVAILABLE`

However, the current Phase M.1 artifact content itself was modified and committed by Phase M.1 commit:

`81d9649`

Therefore the repository now has an actual post-artifact provenance/reporting finalization commit. The claim that provenance finalization is unavailable is not consistent with the Git history.

Do not guess. Verify the actual Git ancestry first. Then classify the SHAs according to their semantic roles.

Expected interpretation, subject to Git-history verification:

- `EXECUTION_CODE_SHA = 30473ee` — pre-data/evaluation blindness boundary.
- `ARTIFACT_CONTENT_COMMIT_SHA = c691672` — original Phase M result artifacts.
- `PROVENANCE_FINALIZATION_COMMIT_SHA = 81d9649` — M.1 post-run provenance/report repair commit.

If Git history shows a different exact semantic boundary, use the verified SHA instead. Never fabricate one.

### Defect B — Data Doctor was not run against the prospective OOS dataset

The reported verification command is:

`run.ps1 doctor-data`

with no explicit OOS data directory or frozen OOS config.

The completion transcript likewise reports:

> all required historical symbols valid and verified

That strongly indicates the default/historical data target was checked, not the prospective dataset used by `bb0887e4`.

The required Phase M data verification is:

`powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor-data -DataDir data/processed_oos -Config configs/v2_oos_frozen.yaml`

Run that exact command.

This is a verification-only action. It is **not** a performance rerun.

The final completion report must state the exact OOS-targeted command and result.

### Defect C — Continuation controls are not wired through the canonical CLI

The runner contains:

- `validate_continuation_chronology(...)`;
- `prior_oos_run_id`;
- `prior_oos_end_timestamp`;

but `build_argument_parser()` / `main()` do not expose or pass the prior-run lineage parameters.

Therefore the documented future continuation path is not fully executable through the canonical Phase M command.

In addition, `validate_evaluation_window_shift()` currently requires the nominal start date to equal `2026-10-01` even when a continuation run should legitimately begin after the prior accepted OOS endpoint.

This must be repaired without changing strategy semantics.

---

# 2. Non-Negotiable Preservation Rules

Do not:

- rerun performance for `bb0887e4`;
- regenerate the two-session result by executing `fidelity-v2-oos`;
- tune any parameter;
- alter V2 strategy economics;
- change the historical control;
- change the two-session P&L;
- add or remove symbols;
- change cost assumptions;
- change margin assumptions;
- change the 20-session scientific threshold.

The existing `bb0887e4` result remains a valid two-session observation.

Its economic values must remain exactly:

- V2-A: +1.21%;
- V2-B: +0.92%;
- V2-C: +0.92%;
- tactical contribution: -$290.98;
- 2 completed tactical round trips;
- peak margin debt: $0.00;
- sample status: `PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE`;
- interpretation: `NEUTRAL / INCONCLUSIVE`.

---

# 3. Repair A — Provenance Finalization

## A1. Verify Git history

Inspect the actual commit history and diffs involving:

- `30473ee`;
- `c691672`;
- `81d9649`.

Use the actual repository history; do not infer based only on report prose.

Establish precisely:

1. which commit contains the pre-evaluation execution code;
2. which commit first persisted the original Phase M result;
3. which commit performed the M.1 reporting/provenance modification.

## A2. Preserve the semantic distinction

The active artifact schema must contain only:

- `execution_code_sha`;
- `artifact_content_commit_sha`;
- `provenance_finalization_commit_sha`;
- optional deprecated `git_sha` alias to execution SHA.

There must be no active `artifact_commit_sha`.

## A3. Correct the already-preserved artifact metadata

Update the Phase M report/JSON/preservation note so the SHA taxonomy reflects actual Git history.

Do not change the performance payload.

Do not change dataset hashes.

Do not change timestamps.

Do not change trade records.

Only provenance metadata may change.

## A4. Add a semantic provenance test

Create a regression test showing that the Phase M.1 artifact can represent:

`execution_code_sha != artifact_content_commit_sha != provenance_finalization_commit_sha`

when all three roles actually exist.

The test should prevent accidental collapsing of post-run repair commits into the execution SHA.

---

# 4. Repair B — Correct OOS Data Doctor Verification

Run the exact command:

`powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor-data -DataDir data/processed_oos -Config configs/v2_oos_frozen.yaml`

Do not substitute the historical defaults.

Record in the completion report:

- exact command;
- exact exit/result status;
- dataset/data directory;
- config path;
- whether the OOS manifest passes.

If the command fails:

1. diagnose the data-validation defect;
2. repair only the verification/data-validation infrastructure;
3. rerun `doctor-data`;
4. do not run performance.

If the OOS data itself is genuinely invalid, classify the Phase M data-validation state accordingly instead of declaring PASS.

---

# 5. Repair C — Wire Continuation Through the Canonical CLI

## C1. Add CLI arguments

Extend `build_argument_parser()` with explicit arguments for continuation lineage:

- `--prior-oos-run-id`
- `--prior-oos-end-timestamp`

These must flow through `main()` into `run_v2_oos_pipeline()`.

The pipeline already accepts these parameters; the missing piece is canonical CLI wiring.

## C2. Enforce paired lineage

If either continuation argument is supplied, require both.

Reject:

- prior run ID without prior endpoint;
- prior endpoint without prior run ID.

This prevents ambiguous continuation lineage.

## C3. New-run identity

A continuation must always generate a fresh run ID.

Never reuse `bb0887e4`.

Never allow the CLI to specify an old accepted run ID as the new output run ID.

The prior run ID is lineage metadata, not the new result identity.

---

# 6. Repair D — Correct Initial-vs-Continuation Window Validation

Current behavior hardcodes the initial date `2026-10-01`.

That is correct for the first prospective run but incorrect for later continuation runs.

Implement two explicitly distinct rules.

## D1. Initial prospective run

When no prior OOS lineage is provided:

- nominal start must remain `2026-10-01`;
- all bars must be strictly after `2026-09-30T23:59:59Z`.

## D2. Continuation run

When prior OOS lineage is provided:

- nominal start must be strictly after the prior accepted OOS endpoint;
- all new bars must be strictly after the prior accepted endpoint;
- all bars must still be strictly after the historical cutoff;
- no overlapping session may be silently re-evaluated.

Do not simply remove the initial date check.

Replace it with an explicit initial/continuation distinction.

---

# 7. Repair E — Make Continuation Data Semantics Explicit

A continuation run must report:

- `prior_oos_run_id`;
- `prior_oos_end_timestamp`;
- `incremental_sessions_count`;
- `cumulative_sessions_count`;
- incremental evaluation interval;
- cumulative prospective chronology;
- dataset ID/hash used for the new run.

The current result model already contains some continuation fields. Verify that:

- they are populated when continuation arguments exist;
- they remain null for the first run;
- they serialize to JSON and Markdown;
- the values are internally consistent.

Do not invent cumulative performance if the runner does not actually possess the prior result needed to calculate it.

At minimum the new run may report incremental performance plus lineage.

If cumulative performance is implemented, ensure it is calculated mechanically from actual persisted run data, not reconstructed from prose.

---

# 8. Repair F — Add Missing Continuation Regression Tests

Add tests for all of the following.

### F1. CLI exposes continuation arguments

The parser must recognize:

- `--prior-oos-run-id`;
- `--prior-oos-end-timestamp`.

### F2. Paired lineage requirement

Supplying only one of the two arguments must fail.

### F3. Initial window remains frozen

No prior lineage + start date other than `2026-10-01` must fail.

### F4. Continuation window may move forward

With prior endpoint `2026-10-02T19:59:00Z`, a new start such as `2026-10-05` must pass the window-rule validator.

### F5. Continuation overlap is rejected

Any bar at or before the prior endpoint must fail.

### F6. Continuation after endpoint is accepted

A synthetic unit fixture with all bars strictly after the prior endpoint must pass chronology validation.

This is a unit-level validation test only. Do not run a performance backtest using synthetic data.

### F7. Historical cutoff still applies

Continuation data at or before 2026-09-30 must fail regardless of the prior endpoint.

### F8. New run ID protection

A continuation cannot overwrite an existing accepted run directory.

### F9. Prior lineage serialization

A continuation result model serializes `prior_oos_run_id` and `prior_oos_end_timestamp`.

### F10. Provenance taxonomy

The continuation result contains no generic `artifact_commit_sha`.

### F11. Frozen strategy fingerprint

Changing any frozen strategy or cost parameter still fails even when the continuation window is valid.

---

# 9. Repair G — Improve the Verification Report

Update the Phase M.1 completion artifact to state exact verification targets.

The verification matrix must contain:

| Check | Exact target |
|---|---|
| Full pytest | `python -m pytest` |
| Targeted OOS | `python -m pytest -v tests/test_v2_oos_validation.py` |
| Ruff | `python -m ruff check .` |
| Doctor | `run.ps1 doctor` |
| **OOS Data Doctor** | `run.ps1 doctor-data -DataDir data/processed_oos -Config configs/v2_oos_frozen.yaml` |
| Git status | `git status --short` |

The report must include actual results, not only PASS labels.

For pytest, record:

- passed;
- skipped;
- failed;
- duration if available.

Do not claim OOS data validation from a default historical-data doctor invocation.

---

# 10. Required Preservation Statement

Add to the preservation note:

> Phase M.1.1 changes only provenance metadata, verification evidence, and continuation-validation infrastructure. It does not rerun the Phase M performance experiment and does not modify the economic observations of Run bb0887e4.

Also preserve the original:

`EXECUTION_CODE_SHA = 30473ee`

as the pre-evaluation blindness boundary.

---

# 11. Prohibited Changes

Do not modify:

- `HEADLINE_UNIVERSE`;
- impulse lookback;
- impulse threshold;
- pullback depth;
- stabilization bars;
- tactical scale-out;
- stop buffer;
- rebound target;
- trend filter;
- leverage;
- maintenance margin;
- margin interest rate;
- equity slippage;
- commissions;
- initial core allocation;
- historical control metrics.

Do not convert this into a strategy-tuning phase.

---

# 12. Verification Commands

Run:

`.\.venv\Scripts\python.exe -m pytest -v tests/test_v2_oos_validation.py`

`.\.venv\Scripts\python.exe -m pytest`

`.\.venv\Scripts\python.exe -m ruff check .`

`powershell -ExecutionPolicy Bypass -File .\run.ps1 test`

`powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor`

`powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor-data -DataDir data/processed_oos -Config configs/v2_oos_frozen.yaml`

`git status --short`

Do **not** execute:

`run.ps1 fidelity-v2-oos`

for this repair.

---

# 13. Required Completion Report

Gemini must report:

## A. Defects found

Explicitly state all three:

1. provenance finalization classification;
2. wrong/default data-doctor target;
3. continuation CLI/window wiring gap.

If any is not applicable after repository verification, explain why with evidence.

## B. Git provenance

Report:

- `EXECUTION_CODE_SHA`;
- `ARTIFACT_CONTENT_COMMIT_SHA`;
- `PROVENANCE_FINALIZATION_COMMIT_SHA`.

Each SHA must have a one-line semantic explanation.

## C. Verification

Report exact results for:

- targeted pytest;
- full pytest;
- Ruff;
- doctor;
- OOS-targeted doctor-data;
- git status.

## D. Preservation

Explicitly confirm:

- `bb0887e4` not performance-rerun;
- economic results unchanged;
- historical `24a9e783` untouched.

## E. Continuation readiness

Demonstrate:

- CLI arguments exist;
- lineage is passed into the pipeline;
- initial date remains frozen;
- future continuation dates are allowed only after prior endpoint;
- overlap is rejected;
- new runs cannot overwrite accepted runs.

## F. Stop statement

State exactly:

`NO PERFORMANCE RERUN OF bb0887e4 PERFORMED`

---

# 14. Acceptance Criteria

Phase M.1.1 is accepted only if all are true:

- [ ] Provenance roles are verified against actual Git history.
- [ ] `PROVENANCE_FINALIZATION_COMMIT_SHA` is populated when a real finalization commit exists.
- [ ] No active generic `artifact_commit_sha`.
- [ ] OOS-targeted `doctor-data` passes.
- [ ] Completion report names the exact OOS data directory and config.
- [ ] Continuation CLI arguments exist.
- [ ] Continuation arguments reach `run_v2_oos_pipeline()`.
- [ ] Initial run still requires 2026-10-01.
- [ ] Continuation runs can legitimately begin after the prior OOS endpoint.
- [ ] Overlap/backward chronology is rejected.
- [ ] New run IDs are mandatory.
- [ ] Existing accepted run artifacts remain protected.
- [ ] Full test suite passes.
- [ ] Ruff passes.
- [ ] Doctor passes.
- [ ] Git status is clean.
- [ ] `bb0887e4` performance was not rerun.
- [ ] Historical control `24a9e783` is untouched.
- [ ] Scientific status remains `NEUTRAL / INCONCLUSIVE`.
- [ ] No strategy parameters were changed.

---

# 15. Final Stop State

After acceptance:

**STOP SOFTWARE CHANGES.**

Phase M.1.1 is an audit/infrastructure repair only.

The next substantive research action remains:

- continue prospective OOS only when genuinely new chronological sessions exist;
- execute Phase N V2-D independently under its frozen option-data gate;
- execute Phase O V2-F independently under its frozen microstructure-data gate.

Do not use the two-session Phase M observation to tune Phase N or Phase O.
