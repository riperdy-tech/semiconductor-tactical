# Reddit V2 Phase M — Post-Run Audit, Provenance Repair, and Prospective Continuation Plan

**Status:** APPROVED FOR GEMINI EXECUTION  
**Phase:** M.1 / Post-run audit and continuation-hardening  
**Scope:** Repair Phase M reporting/provenance and harden the prospective continuation protocol after the first genuine OOS observation.  
**Strategy status:** FROZEN  
**Historical strategy status:** IMMUTABLE  
**Primary OOS run:** `bb0887e4`  
**Historical control:** `24a9e783`

---

## 1. Purpose

Phase M has successfully produced the first genuinely chronological prospective observation after the historical window, but the initial prospective sample contains only two complete sessions.

The result is therefore:

- operationally valid as a prospective observation;
- scientifically insufficient for strategy validation;
- not evidence of either confirmation or refutation;
- not a reason to alter any strategy parameter.

This plan exists to repair the surrounding audit/provenance layer and to make the continuing October prospective process explicit and reproducible.

This is a **research-infrastructure repair**, not a strategy-development phase.

### Non-negotiable conclusion

The existing Phase M result must remain preserved exactly as an observed result:

- V2-A: +1.21%;
- V2-B: +0.92%;
- V2-C: +0.92%;
- tactical contribution: -$290.98;
- 2 tactical round trips;
- 2 complete RTH sessions.

Do **not** rerun the two-session historical/prospective evaluation merely to regenerate the same performance.

Do **not** tune any parameter based on the two-session result.

---

# 2. Ground Truth / Evidence Register

Use these facts as the starting state.

| Item | Current recorded value | Classification |
|---|---|---|
| Historical control run | `24a9e783` | OBSERVED |
| Phase M prospective run | `bb0887e4` | OBSERVED |
| Pre-evaluation execution SHA | `30473ee` | OBSERVED |
| Artifact commitment SHA currently reported | `c691672` | OBSERVED |
| Prospective data start | 2026-10-01 | OBSERVED |
| Prospective end evaluated | 2026-10-02 | OBSERVED |
| Complete sessions | 2 | OBSERVED |
| Minimum conclusive threshold | 20 complete sessions | FROZEN SPEC |
| Provider | Massive Stocks REST API | OBSERVED |
| Dataset ID | `massive_stocks_1m_c857b18f710f` | OBSERVED |
| Dataset aggregate SHA-256 | `c857b18f710fb7f59e82ecdb6816c8524914c8a003e70912196c86ba2edfcac2` | OBSERVED |
| V2-A return | +1.21% | OBSERVED |
| V2-B return | +0.92% | OBSERVED |
| V2-C return | +0.92% | OBSERVED |
| Tactical contribution | -$290.98 | OBSERVED |
| Peak margin debt | $0 | OBSERVED |
| Interpretation | NEUTRAL / INCONCLUSIVE | REQUIRED |
| Strategy validation | NOT ESTABLISHED | REQUIRED |

Do not silently change these values while repairing the reporting layer.

---

# 3. Problems To Repair

There are four distinct repair targets.

## 3.1 Provenance taxonomy is still too generic

The Phase M completion report currently exposes:

`EXECUTION_CODE_SHA`

and

`Artifact Commitment SHA`

The second name is ambiguous.

Bring Phase M into the same explicit provenance taxonomy already established in the earlier L.2/L.2.1/L.2.1.1 audit work.

### Required active provenance fields

Use these names:

- `EXECUTION_CODE_SHA`
- `ARTIFACT_CONTENT_COMMIT_SHA`
- `PROVENANCE_FINALIZATION_COMMIT_SHA`

Optional compatibility field:

- `git_sha` may remain only as a clearly documented deprecated alias of `EXECUTION_CODE_SHA`.

Do **not** create a new generic `artifact_commit_sha` field.

Do **not** reuse one SHA for multiple semantic roles merely for convenience.

### Meaning

#### EXECUTION_CODE_SHA

The exact code/config commit that existed before prospective market data was acquired or evaluated.

It establishes the pre-evaluation blindness boundary.

For the already-preserved Phase M run, the recorded value is:

`30473ee`

Do not rewrite this value merely because later commits exist.

#### ARTIFACT_CONTENT_COMMIT_SHA

The commit that introduced or contains the persisted run artifacts.

This may contain:

- the JSON result;
- Markdown result;
- dataset manifest;
- preservation note;
- related archival files.

It is post-evaluation and therefore must never be represented as the execution code SHA.

#### PROVENANCE_FINALIZATION_COMMIT_SHA

The later commit, if one exists, that finalizes provenance/reporting metadata after the artifact itself was created.

Use it only when there was a distinct finalization commit.

Do not invent a provenance-finalization SHA if no such commit exists.

---

# 4. Repair Scope

Gemini must inspect and, where applicable, repair:

`docs/research/v2_oos/V2_OOS_FROZEN_SPEC.md`

`configs/v2_oos_frozen.yaml`

`src/tactical_engine/research/v2_oos_runner.py`

`tests/test_v2_oos_validation.py`

`reports/v2_oos/bb0887e4.md`

`reports/v2_oos/bb0887e4.json`

`reports/fidelity_runs/v2_oos_bb0887e4/`

any active V2 OOS result schema/model/serializer used by the files above

`run.ps1`

and, if required by the implementation:

`docs/execution_plan/REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md`

Do not modify:

- `reports/V2_HISTORICAL_COMPARISON.md`;
- `reports/v2_historical_comparison.json`;
- Phase L/L.1/L.2 preservation artifacts;
- the frozen V2 strategy parameters;
- the historical Run `24a9e783`;
- the already-preserved two-session Phase M performance numbers.

---

# 5. Repair A — Explicit Provenance Schema

## A1. Locate the active result model

Search for the model/dataclass/schema that serializes the V2 historical/prospective comparison result.

Do not guess the model name.

Identify:

- source model;
- JSON serializer;
- Markdown report generator;
- preservation-note generator;
- tests that validate the result schema.

## A2. Replace ambiguous naming

Where an active field is currently named something equivalent to:

`artifact_commit_sha`

or:

`Artifact Commit SHA`

replace it with the explicit semantic fields described in Section 3.

Do not retain an ambiguous active field merely because older code already uses it.

If backward compatibility is necessary for legacy files, implement it explicitly as a read-only/deprecated migration alias and ensure newly generated artifacts do not emit the ambiguous field.

## A3. Validate semantics

Add tests demonstrating:

1. `EXECUTION_CODE_SHA` is taken from the pre-evaluation execution boundary.
2. `ARTIFACT_CONTENT_COMMIT_SHA` is the post-run artifact commit.
3. `PROVENANCE_FINALIZATION_COMMIT_SHA` is only populated when a real later finalization commit exists.
4. No field claims that a post-run artifact commit was the pre-evaluation execution commit.
5. New JSON and Markdown do not emit a generic `artifact_commit_sha`.

## A4. Do not fabricate Git history

Never derive a SHA by guessing from a report timestamp or file path.

If the existing Phase M artifact genuinely lacks evidence for one of the optional SHA roles, write `null` / `UNAVAILABLE` according to the repository's established schema rather than inventing a value.

---

# 6. Repair B — Exact Verification Summary in Completion Artifacts

The completion report must become independently auditable.

The current transcript shows that pytest, Ruff, doctor, and doctor-data were executed, but the report does not preserve the exact final verification summary.

Add an explicit section:

## Verification Matrix

Include at minimum:

- `pytest`: exact passed/skipped/failed counts;
- targeted OOS tests: exact passed/skipped/failed counts;
- `ruff check .`: PASS/FAIL;
- `run.ps1 doctor`: PASS/FAIL;
- `run.ps1 doctor-data -DataDir ... -Config ...`: PASS/FAIL;
- `git status --short`: CLEAN / NOT CLEAN;
- exact commit SHA containing the final repaired implementation.

Do not write merely “tests passed.”

Record the numerical test count.

If the repository has a canonical verification command such as `run.ps1 test`, use it and report its exact outcome.

### Important

Do not rerun the Phase M performance experiment just to obtain prettier verification metadata.

Verification may be rerun on the repaired code without re-evaluating the OOS performance window, provided the verification command itself does not alter or overwrite the preserved performance artifact.

---

# 7. Repair C — Freeze the Two-Session Result

The already-produced OOS result must be treated as an immutable observation.

## C1. Add overwrite protection

Strengthen tests so that an accepted OOS run cannot be overwritten accidentally.

The protection should cover at least:

- `reports/v2_oos/bb0887e4.json`;
- `reports/v2_oos/bb0887e4.md`;
- its preservation directory;
- its dataset manifest.

A subsequent run must receive a new run ID and new artifact paths.

## C2. Preserve exact content

If the existing files need metadata repairs, make the smallest possible change.

Do not change:

- trade records;
- equity curve;
- returns;
- MDD;
- tactical P&L;
- session dates;
- dataset hash;
- parameter fingerprint.

If an artifact must be regenerated because the schema is being corrected, preserve the original pre-repair artifact under an explicit immutable archive/reference before generating the corrected schema version.

Do not silently overwrite the original.

---

# 8. Repair D — Formalize Prospective Continuation

The biggest protocol ambiguity is the phrase “append new sessions.”

The continuation process must be described more rigorously.

## D1. Define cumulative prospective evaluation

The canonical prospective chronology begins:

`2026-10-01T13:30:00Z`

The historical boundary remains:

`2026-09-30`

New observations may extend the cumulative OOS chronology only forward in time.

The runner must never:

- add timestamps before the prior OOS start;
- replace an already-evaluated session with revised data without a new dataset version and explicit reason;
- move the start date backward;
- shift the evaluation window because of performance;
- silently change configuration.

## D2. Same frozen specification

Every continuation run must retain the same:

- strategy parameters;
- universe;
- cost model;
- margin assumptions;
- signal definitions;
- execution logic;
- accounting model;
- config fingerprint;
- execution-code lineage appropriate to the frozen strategy.

A continuation run may use a **new implementation commit only for non-strategy infrastructure fixes**, and the report must state exactly what changed.

## D3. No retroactive tuning

Once any OOS performance has been observed, Gemini must not alter:

- impulse lookback;
- impulse magnitude;
- pullback depth;
- stabilization bars;
- scale-out fraction;
- stop type;
- rebound target;
- core allocation;
- leverage;
- margin assumptions;
- cost configuration;
- symbol universe.

Do not add symbols because they perform well.

Do not remove symbols because they perform poorly.

Do not alter the 20-session threshold.

## D4. New runs require new IDs

Every continuation evaluation gets a new run ID.

Never update `bb0887e4` in place.

The cumulative report should identify:

- prior accepted OOS run(s);
- newly added chronological interval;
- cumulative interval;
- dataset/version hashes;
- code lineage;
- strategy/config fingerprint.

---

# 9. Repair E — Continuation-Test Suite

Add regression tests covering the continuation protocol.

At minimum:

### Test 1 — Historical boundary

A continuation dataset containing a bar at or before 2026-09-30 must fail validation.

### Test 2 — No backwards chronology

A continuation dataset whose earliest new bar precedes the prior accepted OOS endpoint must fail.

### Test 3 — Frozen strategy fingerprint

A continuation with any changed frozen strategy parameter must fail.

### Test 4 — Frozen cost configuration

A continuation with a changed cost configuration must fail.

### Test 5 — Frozen universe

A continuation with symbols outside the approved V2 headline universe must fail unless explicitly covered by an already-approved manifest policy.

### Test 6 — New run ID

Continuation execution cannot overwrite an existing accepted run artifact.

### Test 7 — Dataset lineage

The result must record both the dataset ID and aggregate dataset hash.

### Test 8 — Provenance lineage

The result must expose the explicit SHA taxonomy from Section 3.

### Test 9 — No performance-based window shifting

Any requested evaluation start that differs from the frozen prospective boundary must require an explicit invalidation/error rather than silently adapting.

### Test 10 — No-lookahead

Continuation execution preserves the same chronological no-lookahead guarantees as the primary OOS run.

---

# 10. Repair F — Prospective Sample Classification

Keep the classification logic explicit and deterministic.

For the existing two-session result:

`PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE`

and:

`NEUTRAL / INCONCLUSIVE`

remain unchanged.

The classification must not depend on the sign of the return.

Examples:

- 2 sessions, +20% → still insufficient;
- 2 sessions, -20% → still insufficient;
- 19 sessions → still insufficient if the frozen minimum is 20;
- 20+ complete sessions → eligible for the preregistered conclusive analysis.

Do not create a new “promising” or “failed” classification based merely on cumulative return.

---

# 11. Repair G — Report Wording

The Phase M report should explicitly distinguish:

### Observation

“What happened in the two observed sessions.”

### Scientific interpretation

“What can and cannot be inferred from those observations.”

### Prospective status

“Chronologically valid OOS, but insufficient sample.”

### Strategy status

“Full Reddit replication remains unestablished.”

Use language equivalent to:

> The October 1–2, 2026 observations are genuine prospective observations because they occur strictly after the frozen historical window. They are retained as valid OOS monitoring data. However, only two complete regular sessions are available, below the preregistered 20-session threshold; therefore the result is NEUTRAL / INCONCLUSIVE and cannot confirm or reject the historical edge.

Do not say:

- “the strategy failed”;
- “the strategy works”;
- “the edge disappeared”;
- “the OOS proved robustness.”

---

# 12. Repair H — Separate Performance From Infrastructure Validation

The completion report must not blur these two questions:

### Question 1

Did the engine successfully execute the prospective experiment?

Expected answer:

**Yes**, subject to the final verification matrix.

### Question 2

Did the strategy demonstrate out-of-sample alpha?

Expected answer:

**Not yet — insufficient sample.**

Both can be true simultaneously.

---

# 13. Required Tests and Verification

Before finalizing the repair:

Run the repository's normal full test suite.

Also run the targeted OOS test file(s).

Run:

`..venvScriptspython.exe -m ruff check .`

Run:

`powershell -ExecutionPolicy Bypass -File .un.ps1 doctor`

Run:

`powershell -ExecutionPolicy Bypass -File .un.ps1 doctor-data -DataDir data/processed_oos -Config configs/v2_oos_frozen.yaml`

Run:

`git status --short`

Do **not** launch another `fidelity-v2-oos` performance evaluation merely because the repair changed report/provenance code.

If a code change genuinely affects calculation semantics rather than only provenance/reporting/continuation validation, stop and classify it as a strategy-affecting defect. Do not hide it under this repair package.

---

# 14. Required Artifact Updates

Gemini must produce or update:

1. `docs/research/v2_oos/V2_OOS_FROZEN_SPEC.md`
   - only where continuation/provenance semantics need clarification.

2. `src/tactical_engine/research/v2_oos_runner.py`
   - only for provenance/continuation validation and overwrite protections.

3. Active V2 OOS result schema/model/serializer.
   - explicit provenance taxonomy.

4. `tests/test_v2_oos_validation.py`
   - schema, provenance, chronology, continuation, overwrite tests.

5. `reports/v2_oos/bb0887e4.md`
   - corrected provenance labels and verification matrix if the repository's artifact policy permits an in-place metadata repair.

6. `reports/v2_oos/bb0887e4.json`
   - corrected schema only; no performance changes.

7. `reports/fidelity_runs/v2_oos_bb0887e4/PRESERVATION_NOTE.md`
   - explicitly describe that the performance result is preserved and that this repair changes audit metadata/protocol only.

8. A new preservation/audit note if needed for the repaired artifact lineage.

---

# 15. No-Run Rule

This package is **not** authorized to produce another performance result for the October 1–2 window.

Do not:

`fidelity-v2-oos` the same two-day window again merely to regenerate the artifact.

Do not:

- tune parameters;
- alter the common universe;
- change cost settings;
- change margin assumptions;
- add a benchmark because it looks better;
- exclude trades because they look anomalous;
- choose a more favorable OOS start/end date.

The next performance observation must come from genuinely new chronological market sessions after the already-observed period.

---

# 16. When A New Performance Run Is Eventually Allowed

A new prospective evaluation is allowed only when new chronological market data exists.

The run must:

1. start strictly after the prior accepted OOS endpoint;
2. use the frozen strategy specification;
3. use the same approved universe;
4. use the same execution/economic assumptions;
5. produce a new run ID;
6. preserve the earlier run unchanged;
7. record the complete provenance chain;
8. report the cumulative and incremental intervals separately.

Example:

- Existing accepted observation: Oct 1–2.
- New data: Oct 5 onward.
- Valid new prospective interval: Oct 5 forward.
- Invalid: rerunning Oct 1–2 because the result was negative.

---

# 17. Phase M Scientific Gate

The repaired infrastructure is considered complete only when:

- provenance taxonomy is explicit;
- report verification is numerically auditable;
- accepted artifacts cannot be silently overwritten;
- continuation chronology is enforced;
- frozen strategy fingerprints are enforced;
- no-lookahead remains tested;
- the existing two-session result remains numerically unchanged;
- historical control remains untouched;
- full tests and static checks are clean.

The scientific Phase M gate remains separate.

### Current status

`PRISTINE_OOS = VALID_BUT_INSUFFICIENT_SAMPLE`

`INTERPRETATION_CLASS = NEUTRAL / INCONCLUSIVE`

`STRATEGY_VALIDATION = NOT_ESTABLISHED`

`STRATEGY_REFUTATION = NOT_ESTABLISHED`

Do not promote these statuses because of the repair.

---

# 18. Required Gemini Completion Report

Return a completion report containing:

## A. Repair summary

- exact defects found;
- files changed;
- why each change was necessary.

## B. Provenance

Report exactly:

`EXECUTION_CODE_SHA = ...`

`ARTIFACT_CONTENT_COMMIT_SHA = ...`

`PROVENANCE_FINALIZATION_COMMIT_SHA = ... or UNAVAILABLE`

Do not use an ambiguous generic Artifact Commit SHA.

## C. Existing result preservation

State explicitly:

- Run ID `bb0887e4` preserved;
- V2-A unchanged at +1.21%;
- V2-B unchanged at +0.92%;
- V2-C unchanged at +0.92%;
- tactical contribution unchanged at -$290.98;
- 2 complete sessions unchanged.

## D. Validation

Report:

- full pytest exact counts;
- targeted pytest exact counts;
- Ruff status;
- doctor status;
- doctor-data status;
- git status.

## E. Continuation protocol

State:

- what prevents backward chronology;
- what prevents parameter drift;
- what prevents artifact overwrite;
- how a future new OOS run receives a new run ID.

## F. Performance rerun statement

Explicitly state:

`NO PERFORMANCE RERUN OF bb0887e4 PERFORMED`

unless a true engine-calculation defect is discovered.

## G. Stop state

After completing this repair:

**STOP.**

Do not begin options or Level-2 implementation from this package.

The existing Phase N and Phase O execution plans remain separately frozen.

---

# 19. Failure / Escalation Rules

Stop and report instead of improvising if any of the following are discovered:

- the current two-day result cannot be reproduced without changing strategy logic;
- the reported `EXECUTION_CODE_SHA` does not actually precede data acquisition;
- the persisted dataset differs from its reported aggregate SHA;
- the result artifact contains fields that cannot be reconciled to actual Git history;
- the current runner silently changes frozen parameters;
- continuation requires changing strategy semantics;
- the first OOS run was accidentally overwritten or materially modified;
- the report's performance values differ from the preserved JSON/run artifact.

These are audit findings, not reasons to “fix the numbers.”

---

# 20. Final Acceptance Checklist

Gemini must check every box before declaring completion:

- [ ] Existing Phase M run `bb0887e4` preserved.
- [ ] Historical Run `24a9e783` untouched.
- [ ] No strategy parameter changes.
- [ ] No performance rerun of the two-session window.
- [ ] Explicit SHA taxonomy implemented.
- [ ] No active generic `artifact_commit_sha`.
- [ ] Exact verification counts recorded.
- [ ] Continuation chronology enforced.
- [ ] Frozen parameter fingerprint enforced for continuation.
- [ ] New run IDs required.
- [ ] Accepted artifacts cannot be overwritten.
- [ ] OOS boundary remains after 2026-09-30.
- [ ] Two-session result remains NEUTRAL / INCONCLUSIVE.
- [ ] Full test suite passes.
- [ ] Ruff passes.
- [ ] Doctor passes.
- [ ] Doctor-data passes.
- [ ] Working tree clean.
- [ ] Completion report includes exact provenance.
- [ ] Completion report explicitly states no performance rerun.
- [ ] Global epistemic status remains unchanged.

---

# 21. Stop State

After this package is accepted:

**Engineering repair is complete.**

The next work remains:

1. Continue chronological Phase M monitoring as genuinely new sessions become available.
2. Independently execute Phase N V2-D covered-call research under its frozen option-data gate.
3. Independently execute Phase O V2-F Level-2 research under its frozen microstructure-data gate.

Do not use this two-session OOS result to tune either Phase N or Phase O.

Do not declare the Reddit strategy replicated.

