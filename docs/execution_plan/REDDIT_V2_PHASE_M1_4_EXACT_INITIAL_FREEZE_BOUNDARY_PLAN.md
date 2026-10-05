# Reddit V2 Phase M.1.4 — Exact Initial Freeze-Boundary Enforcement

**Status:** REQUIRED FINAL REPAIR  
**Phase:** M.1.4  
**Scope:** Correct the remaining initial-run date-freeze validation gap in the Phase M continuation runner.

## 1. Audit Finding

M.1.3 correctly introduced:
- --start;
- --end;
- continuation-only date overrides;
- frozen-YAML integrity;
- forward chronology checks;
- effective-window slicing.

However, the actual initial-run validator compares supplied dates to the frozen configuration by **calendar date only**.

Current behavior permits an initial start such as 2026-10-01T13:30:00Z against frozen 2026-10-01T00:00:00Z, and an initial end such as 2026-10-31T12:00:00Z against frozen 2026-10-31T23:59:59Z.

That violates the M.1.3 requirement that an initial CLI override must match the frozen configuration boundary exactly.

## 2. Non-Negotiable Rules

Do not rerun bb0887e4, alter its economics, alter V2 strategy parameters, change the frozen YAML, change the historical control, or change continuation semantics except where required by this validator repair.

## 3. Required Semantics

### Initial run
- If --start is omitted, use frozen config start.
- If --start is supplied, normalized instant must exactly equal frozen config start.
- If --end is omitted, use frozen config end.
- If --end is supplied, normalized instant must exactly equal frozen config end.
- Do not compare only calendar dates.

Examples:
- 2026-10-01T00:00:00Z: PASS.
- 2026-10-01T00:01:00Z: FAIL.
- 2026-10-01T13:30:00Z: FAIL.
- 2026-10-31T23:59:58Z: FAIL.
- 2026-11-01T00:00:00Z: FAIL.

A date-only 2026-10-01 may normalize to midnight UTC and therefore passes only when it exactly equals the frozen instant.

### Continuation
- Explicit --start and --end remain mandatory.
- start must be strictly after the historical cutoff.
- start must be strictly after the prior accepted OOS endpoint.
- end must be strictly after start.
- Do not apply the initial-boundary equality rule to continuation.

## 4. Implementation

Use the existing _parse_iso_or_date helper.

Compare normalized datetimes, conceptually:
- _parse_iso_or_date(start) == _parse_iso_or_date(frozen_config_start)
- _parse_iso_or_date(end) == _parse_iso_or_date(frozen_config_end)

Do not introduce raw string comparison.

## 5. Regression Tests

Add tests for:
1. exact initial start passes;
2. start one minute later fails;
3. same-day intraday start fails;
4. exact initial end passes;
5. end one second earlier fails;
6. end one second later fails;
7. date-only input normalization;
8. equivalent timezone instant;
9. valid forward continuation;
10. continuation overlap rejection;
11. frozen YAML SHA remains be21c7dc0f998cf21310ffb5ffeae39fe039046d80aaa4ee4c656189f44f502a;
12. strategy fingerprint remains unchanged.

## 6. Verification

Run:

.\.venv\Scripts\python.exe -m pytest -v tests/test_v2_oos_validation.py

.\.venv\Scripts\python.exe -m pytest

.\.venv\Scripts\python.exe -m ruff check .

powershell -ExecutionPolicy Bypass -File .\run.ps1 test

powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor

powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor-data -DataDir data/processed_oos -Config configs/v2_oos_frozen.yaml

git status --short

Do not execute run.ps1 fidelity-v2-oos.

## 7. Preservation

Confirm unchanged:
- Run bb0887e4;
- V2-A +1.21%;
- V2-B +0.92%;
- V2-C +0.92%;
- tactical contribution -$290.98;
- two complete sessions;
- NEUTRAL / INCONCLUSIVE;
- historical Run 24a9e783;
- frozen YAML SHA256.

## 8. Completion Report

Report exact implementation change, normalization semantics, tests added, verification results, frozen-config SHA, and:

NO PERFORMANCE RERUN OF bb0887e4 PERFORMED

## 9. Acceptance Criteria

- Initial start comparison is exact after normalization.
- Initial end comparison is exact after normalization.
- Same-day intraday shifts are rejected.
- Continuation windows still permit future dates.
- Continuation overlap remains rejected.
- Frozen YAML unchanged.
- Strategy fingerprint unchanged.
- Targeted tests pass.
- Full tests pass.
- Ruff passes.
- Canonical test passes.
- Doctor passes.
- OOS doctor-data passes.
- Working tree clean.
- No performance rerun.

## 10. Final Stop State

After M.1.4 passes: **STOP SOFTWARE CHANGES.**

This closes the remaining known Phase M initial-boundary validation defect. Future work should be genuine prospective monitoring only.