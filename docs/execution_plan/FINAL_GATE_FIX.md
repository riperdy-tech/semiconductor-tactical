# Final Gate Fix + Next Steps

**Date:** 2026-10-02  
**Baseline:** commit `7236ed0`

This is a small corrective pass after the main research-integrity package.

## Objective

Fix the remaining CLI integrity bug and one methodology detail. Then stop software changes unless a new evidence-driven issue is found.

### Fix 1 — Historical refusal must return non-zero

Current behavior:
- `run_historical_backtest(..., raise_on_refusal=False)` prints "REFUSED EXECUTION" and returns.
- `run_historical_comparison(..., raise_on_refusal=False)` does the same.
- The PowerShell runner therefore can report process success even when the research gate rejected the dataset.

Required behavior:

- command-line invocation of `historical` on unverified/synthetic data => non-zero exit code;
- command-line invocation of `comparison-historical` on unverified/synthetic data => non-zero exit code;
- Python-level helper tests may retain a non-raising mode only if there is a clear reason, but CLI `main()` must convert refusal into `SystemExit(1)` or an equivalent non-zero process result.

Add integration tests that launch the actual CLI/subprocess or exercise the exact `main()` path and assert non-zero exit status.

Acceptance:
```
.\run.ps1 historical                 -> FAIL/REFUSED on bundled sample data
.\run.ps1 comparison-historical     -> FAIL/REFUSED on bundled sample data
$LASTEXITCODE                         -> non-zero
```

Do not make fixture-validation commands fail. These remain valid:
```
.\run.ps1 backtest
.\run.ps1 research
.\run.ps1 comparison
```

## Fix 2 — Strategy daily bootstrap should preserve the daily time axis

Current strategy bootstrap groups realized P&L by days on which trades exit. This omits inactive sessions.

Required refinement:

- build a complete session/day axis over the evaluation period;
- assign zero strategy return to sessions with no realized trading P&L;
- retain explicit timezone/session assumptions;
- resample the complete daily strategy-return series;
- keep the `INSUFFICIENT_SAMPLE` rule.

If the existing data structures make a clean complete-day reconstruction awkward, document the limitation rather than inventing one.

The report must say exactly what constitutes one observation.

## Fix 3 — Make final OOS robustness scope explicit

The final report should clearly distinguish:

- full-sample diagnostics;
- train diagnostics;
- validation diagnostics;
- untouched final test/OOS diagnostics.

Do not imply that a full-sample ticker exclusion test is a test-period falsification test.

For every robustness result, include a period field such as:
- `FULL`
- `TRAIN`
- `VALIDATION`
- `TEST_OOS`

Where a diagnostic is intentionally full-sample only, say so.

## Required validation

Run:
- `python -m pytest`
- `python -m ruff check .`
- `.un.ps1 doctor`
- `.un.ps1 doctor-data`
- `.un.ps1 backtest`
- `.un.ps1 comparison`
- `.un.ps1 historical` (must refuse with non-zero)
- `.un.ps1 comparison-historical` (must refuse with non-zero)

CI must pass.

## Stop condition

After this pass, do not continue changing strategy logic merely for polish.

The software phase is complete enough to ingest genuine market data.

The next workstream is DATA ACQUISITION AND VERIFICATION.
