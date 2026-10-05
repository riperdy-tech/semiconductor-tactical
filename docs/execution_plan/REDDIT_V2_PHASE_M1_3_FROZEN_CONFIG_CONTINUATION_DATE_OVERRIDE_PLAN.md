# Reddit V2 Phase M.1.3 — Frozen-Config Continuation Date Override

**Status:** REQUIRED FINAL RESEARCH-INFRASTRUCTURE REPAIR  
**Phase:** M.1.3  
**Purpose:** Make the already-implemented continuation mechanism operational without editing the frozen OOS configuration file between prospective observations.

---

## 1. Audit Finding

Phase M.1.2 correctly implemented:

- paired continuation lineage;
- overlap/backward chronology rejection;
- forward continuation validation;
- new run IDs;
- OOS data-doctor verification;
- provenance sealing.

However, the canonical runner still derives:

`nominal_date_range`

and the evaluation start from:

`configs/v2_oos_frozen.yaml -> research.start / research.end`

The committed frozen config currently contains:

- `research.start = 2026-10-01T00:00:00Z`
- `research.end = 2026-10-31T23:59:59Z`

The runner's continuation logic can accept a later start in principle, but the canonical CLI does not provide a way to supply that later interval without modifying the frozen YAML.

That is undesirable because the config is explicitly part of the frozen OOS research specification.

### Conclusion

Continuation is **validated at the function level but not yet operationally complete at the canonical command level**.

Do not solve this by editing the frozen YAML for each new OOS period.

---

# 2. Non-Negotiable Preservation Rules

Do not:

- rerun `bb0887e4`;
- alter its economic results;
- alter the historical Run `24a9e783`;
- change any strategy, cost, leverage, universe, or signal parameter;
- modify the frozen research specification's strategy semantics;
- change the October 1 initial OOS boundary;
- rewrite the original dataset;
- create a performance result solely for testing the date override.

This package changes only date-window plumbing for future continuation runs.

---

# 3. Design Requirement

Introduce explicit continuation-only CLI date overrides.

Recommended arguments:

`--start`

`--end`

These should be optional.

### Initial-run behavior

When no prior continuation lineage is supplied:

- use the frozen config dates;
- `--start` / `--end` may be omitted;
- if supplied, they must equal the frozen config dates exactly;
- the initial run therefore cannot shift the evaluation window.

### Continuation behavior

When both:

- `--prior-oos-run-id`
- `--prior-oos-end-timestamp`

are supplied:

- `--start` is required;
- `--end` is required;
- the supplied start/end apply only to the current incremental observation window;
- the underlying strategy/config parameters remain frozen.

The frozen YAML must remain unchanged.

---

# 4. CLI Semantics

Add:

`--start`

Description:

> Continuation evaluation start timestamp/date. For initial runs this must match the frozen config start exactly. For continuation runs it must be strictly after prior accepted OOS endpoint and the historical cutoff.

Add:

`--end`

Description:

> Continuation evaluation end timestamp/date. For initial runs this must match the frozen config end exactly. For continuation runs it must be after the supplied start and must not precede the available verified data.

Do not permit a continuation `--start` or `--end` to alter strategy parameters.

---

# 5. Config Precedence

Use this precedence:

### No continuation lineage

`CLI date -> must equal frozen config date -> effective date`

If omitted:

`frozen config date -> effective date`

### Continuation lineage present

`CLI start/end -> effective date window`

The YAML date fields remain unchanged.

Do not mutate the loaded config object and serialize it back to disk.

Do not write the continuation date into `configs/v2_oos_frozen.yaml`.

---

# 6. Validation Rules

Implement a dedicated validator, e.g.:

`validate_evaluation_window(...)`

with these rules.

## Initial run

- start == frozen config start;
- end == frozen config end;
- start > historical cutoff;
- end > start.

## Continuation run

- both start and end are present;
- start > historical cutoff;
- start > prior accepted OOS endpoint;
- end > start;
- no bar may be <= prior accepted OOS endpoint;
- no bar may be <= historical cutoff.

Reject all violations with explicit `V2OOSEvaluationError` or the existing chronology exception hierarchy.

---

# 7. Do Not Change the Frozen YAML

The following file must remain byte-identical:

`configs/v2_oos_frozen.yaml`

Do not edit its `research.start` or `research.end` to follow October chronology.

The frozen file represents the original preregistered Phase M specification.

A continuation's observation window is execution metadata, not a new strategy specification.

---

# 8. Effective Window Must Flow Through the Engine

Currently the runner uses:

`cfg.research.start`

and:

`cfg.research.end`

for:

- validation;
- result metadata;
- `nominal_date_range`;
- potentially the backtest data filtering.

Introduce local execution-window variables, for example:

`effective_research_start`

`effective_research_end`

Then ensure all relevant calls use those values.

Do not alter the underlying strategy parameter object.

The backtest should receive the correct continuation data interval while preserving identical strategy/economic assumptions.

---

# 9. Result Metadata

The result should distinguish:

### Frozen strategy/config identity

The existing frozen V2 configuration remains the strategy identity.

### Current observation window

Record the actual incremental interval being evaluated:

- `nominal_date_range`;
- `effective_evaluation_start`;
- `evaluation_end_timestamp`.

For a continuation result:

- `prior_oos_run_id`;
- `prior_oos_end_timestamp`;
- `incremental_sessions_count`;
- `cumulative_sessions_count`.

Do not label the continuation as a fresh preregistration.

It is a continuation of the already frozen prospective experiment.

---

# 10. Regression Tests

Add tests for at least:

### T1 — Initial dates default to frozen YAML

No lineage and no CLI override uses the YAML dates.

### T2 — Initial CLI date mismatch rejected

No lineage + `--start 2026-10-02` must fail.

### T3 — Initial end mismatch rejected

No lineage + modified `--end` must fail.

### T4 — Continuation requires explicit dates

Lineage supplied but `--start` or `--end` omitted must fail.

### T5 — Forward continuation accepted

Example:

- prior endpoint: `2026-10-02T19:59:00Z`;
- start: `2026-10-05T00:00:00Z`;
- end: `2026-10-05T23:59:59Z`.

The date validator must accept the window.

### T6 — Continuation start overlap rejected

Start <= prior endpoint must fail.

### T7 — Continuation end before start rejected

End <= start must fail.

### T8 — Historical cutoff still enforced

A continuation start on/before 2026-09-30 must fail.

### T9 — Frozen YAML untouched

Regression test should verify the canonical frozen config remains unchanged by the continuation date plumbing.

Do not make a test that actually modifies the file.

### T10 — Effective date reaches result metadata

A continuation execution using a mocked backtest path should produce the requested effective interval in its result metadata.

### T11 — Strategy fingerprint unchanged

Date overrides must not affect the frozen signal/cost/leverage fingerprint.

### T12 — Existing run protection

Continuation date override cannot reuse an accepted run ID.

---

# 11. Verification Commands

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

Do **not** execute a prospective continuation backtest using synthetic data.

Do **not** execute a new real-market performance run for this repair.

---

# 12. Existing Artifact Preservation

The following must remain economically unchanged:

`bb0887e4`

- V2-A +1.21%;
- V2-B +0.92%;
- V2-C +0.92%;
- tactical contribution -$290.98;
- 2 complete sessions;
- peak margin debt $0;
- interpretation NEUTRAL / INCONCLUSIVE.

The following must remain untouched:

`24a9e783`

Do not regenerate the historical reports.

---

# 13. Frozen Config Integrity

Before and after implementation, compute a hash or byte comparison of:

`configs/v2_oos_frozen.yaml`

The final completion report must state that no content change occurred.

Do not add timestamps, continuation values, or mutable execution state to this frozen file.

---

# 14. Completion Report

Gemini must report:

### A. Design

- exact CLI flags added;
- precedence rules;
- initial vs continuation semantics.

### B. Validation

- exact tests added;
- exact targeted/full pytest counts;
- Ruff;
- canonical test;
- doctor;
- OOS doctor-data.

### C. Frozen-config proof

State:

`configs/v2_oos_frozen.yaml = UNCHANGED`

and provide the before/after hash if available.

### D. Preservation

State exactly:

`NO PERFORMANCE RERUN OF bb0887e4 PERFORMED`

### E. Continuation readiness

Demonstrate through unit tests that:

- initial run cannot shift dates;
- continuation can move forward;
- overlap is rejected;
- the frozen YAML is not modified;
- date overrides affect only the observation interval.

---

# 15. Acceptance Criteria

M.1.3 is accepted only if:

- [ ] Initial run still derives dates from frozen YAML.
- [ ] Initial CLI date changes are rejected.
- [ ] Continuation can supply new start/end without editing frozen YAML.
- [ ] Continuation dates are strictly after prior accepted endpoint.
- [ ] Historical cutoff remains enforced.
- [ ] End must be after start.
- [ ] Effective continuation dates reach the backtest/report metadata.
- [ ] Frozen strategy parameters remain unchanged.
- [ ] Frozen YAML is byte-identical.
- [ ] New run IDs remain mandatory.
- [ ] Existing accepted runs remain protected.
- [ ] Targeted tests pass.
- [ ] Full tests pass.
- [ ] Ruff passes.
- [ ] Doctor passes.
- [ ] OOS doctor-data passes.
- [ ] Working tree is clean.
- [ ] No performance rerun occurred.

---

# 16. Final Stop State

After M.1.3 is accepted:

**STOP SOFTWARE CHANGES.**

The Phase M infrastructure is fully continuation-ready.

Future Phase M activity should consist only of genuinely new chronological market sessions using:

- the immutable frozen strategy specification;
- the immutable frozen config;
- explicit continuation observation dates;
- a new run ID;
- prior-run lineage.

Then proceed to the already approved research tracks N and O independently.
