# Gemini Implementation Instructions — Post-Audit Research Gate

**Date:** 2026-10-02  
**Repository:** `riperdy-tech/semiconductor-tactical`  
**Purpose:** authoritative implementation brief for the next Gemini coding pass.

## 0. Mission

Continue implementation from the current repository state. Do **not** treat the project as research-ready yet.

The engineering layer is substantially complete, but the empirical research pipeline still has unresolved correctness gates. Your job is to close those gates in code, tests, CLI workflow, documentation, and CI.

Do not manufacture market data, option data, or research results.

Use the existing strategy specification and backtest protocol as authoritative. Preserve the distinction:

- **fixture validation** = proves the software works;
- **historical research** = evidence from genuine market data;
- **options research** = UNVALIDATED until genuine historical option-chain quotes exist.

Read first:
1. `README.md`
2. `AGENTS.md`
3. `docs/STRATEGY_SPEC.md`
4. `docs/BACKTEST_PROTOCOL.md`
5. `docs/DATA_CONTRACT.md`
6. `docs/IMPLEMENTATION_PLAN.md`
7. `docs/AUDIT_20261002_POST_GEMINI.md`
8. this file

## 1. Highest-priority correctness issue: regime-adapted comparison

The current historical 3-variant runner loads the strategy universe but does not automatically include `SMH` and `SPY`.

As a result, `run_backtest()` may not construct `BenchmarkRegimeProvider`, and `regime_adapted` can fall back to the per-symbol `trend_ok` behavior.

This is **not** an acceptable implementation of the intended benchmark-based regime variant.

### Required fix

The canonical historical comparison must load the required benchmark inputs alongside the tradable universe:

- MU
- SNDK
- SKHY
- AMD
- USD
- SMH
- SPY

The regime-adapted variant must explicitly use the benchmark regime provider.

Do not silently substitute per-symbol trend for benchmark regime logic.

Add tests proving that:
1. SMH/SPY are loaded for historical comparison;
2. `regime_adapted` receives the benchmark regime provider;
3. changing benchmark regime state can change the regime-adapted signal/result while the other variants remain unchanged where appropriate.

## 2. Real-data readiness

The repository still contains only synthetic sample historical data under `data/sample_historical`.

Do **not** label this dataset as real research.

The code must be ready to consume genuine CSV data supplied later, but do not fabricate or download arbitrary market data merely to make the gate appear complete.

### Required behavior

A real-data run must verify:

- source/provider;
- exact symbols;
- date range;
- bar resolution;
- timezone;
- adjustment/corporate-action policy;
- file SHA-256 hashes;
- configuration hash;
- git commit;
- transaction-cost model;
- slippage model.

Do not infer “REAL_HISTORICAL” merely from a directory name. Provenance/status should be explicit and source-driven.

Avoid a design where placing synthetic CSVs in a differently named directory causes the manifest to claim real market data.

Prefer an explicit dataset metadata/provenance contract.

## 3. Bar cadence validation

Keep the new cadence validation, but make it research-safe.

It must distinguish expected cadence from normal market-session gaps. In particular:

- 1-minute data should be validated as 1-minute bars within valid sessions;
- daily data should be validated as daily bars;
- overnight/weekend/holiday gaps must not be treated as broken 1-minute data;
- regular-session timestamps/timezone must be handled consistently.

Add tests for:
- valid 1m session data;
- valid daily data;
- daily data under 1m config => reject;
- intraday data under 1d config => reject;
- large legitimate overnight/weekend gaps => do not falsely reject.

## 4. Canonical historical comparison

`comparison-historical` must be the authoritative comparison command.

It must:

1. load one identical verified dataset;
2. run:
   - `literal_clone`
   - `risk_controlled`
   - `regime_adapted`
3. use the intended benchmark regime inputs;
4. use identical date boundaries;
5. produce machine-readable JSON;
6. produce Markdown;
7. persist a complete manifest;
8. clearly label synthetic fixture runs versus real historical runs.

Do not claim the Reddit-period reproduction is complete until genuine historical data has been supplied and the run has been executed on it.

## 5. Out-of-sample research is mandatory

Do not optimize parameters on the full historical period and then call the result out-of-sample.

The historical research configuration must support explicit:

- training period;
- validation period;
- test/out-of-sample period.

The final Reddit-period evaluation must report the OOS period separately from development/tuning periods.

Parameter choices must be frozen before the final OOS run.

If the source post's exact trading dates cannot be reconstructed, say so and define the nearest defensible period explicitly.

## 6. Falsification suite: integrate it, do not merely provide helper functions

The repository now has:

- stationary block bootstrap;
- ticker exclusion;
- strongest-day exclusion.

These must become part of the canonical historical research workflow.

The final research report should include, where data permits:

- ticker leave-one-out results;
- strongest-day exclusion;
- block-bootstrap confidence interval / probability-positive;
- cost sensitivity;
- leverage sensitivity;
- parameter perturbation;
- random-entry control;
- regime decomposition;
- trade-count/sample-size diagnostics.

A helper function plus unit tests is **not** enough if the canonical report never executes it.

### Methodological requirement

Be precise about what each test means.

For example, strongest-day exclusion should be described as an attribution/stability diagnostic unless the strategy is actually re-run with those days excluded.

Do not overstate what a robustness test proves.

## 7. Experiment matrix must match implementation

The documentation and code must describe the same experiment grid.

Current mismatch to correct:

- documented leverage: 1.0x, 1.25x, 1.5x, 2.0x, 3.0x;
- current comparison code uses only 1.0x, 1.5x, 2.0x.

Current documented cost sensitivity includes 0/5/10/15 bps, while implementation must be checked to ensure the same grid is actually run.

Either implement the documented matrix or explicitly revise the documentation based on the actual intended matrix. Do not leave a false checklist.

## 8. Event/earnings filter

The event filter is currently structural but no genuine event/earnings feed is connected to the standard historical pipeline.

Do not claim event protection is validated.

Keep it explicitly UNVALIDATED/PARTIAL until an actual event dataset and timestamp-aware blackout mechanism exist.

Do not silently populate events with fabricated data.

## 9. Options

Covered-call mechanics are implemented, but genuine historical option chains are absent.

Rules:

- no Black-Scholes substitution as historical executable quotes;
- no fabricated historical bid/ask;
- option results remain `UNVALIDATED` without genuine historical chains;
- equity-only research may proceed independently.

When option data eventually exists, preserve timestamped bid/ask, strike, expiration, volume/open interest where available, underlying price, and source provenance.

## 10. Provenance/status model

Strengthen `RunManifest` so status is not guessed from the path.

A historical run should explicitly carry a dataset identity such as:

- `SYNTHETIC_SAMPLE_FIXTURE`
- `REAL_HISTORICAL_UNVERIFIED_SOURCE`
- `REAL_HISTORICAL_VERIFIED`

Use whatever naming fits the existing architecture, but make the distinction explicit and enforceable.

The canonical research report must refuse or clearly downgrade evidence when the dataset has not passed the real-data verification gate.

## 11. Do not modify strategy intent silently

Do not tune the strategy to produce attractive returns.

Do not optimize directly against the Reddit headline result.

Do not change pullback thresholds, leverage, layer count, exits, filters, or costs merely because one choice performs better.

Any non-trivial strategy-spec change requires:

- entry in `docs/DECISIONS.md`;
- separate experiment;
- updated tests;
- updated documentation.

## 12. Required acceptance criteria

The task is complete only when all of the following are true:

### Code
- benchmark regime data is correctly wired into `regime_adapted`;
- historical runner and comparison runner share a correct dataset/provenance contract;
- cadence validation handles sessions correctly;
- provenance cannot be spoofed by directory naming;
- OOS boundaries are supported and reported;
- falsification diagnostics are integrated into the canonical research output;
- experiment matrix and documentation agree.

### Tests
Add deterministic tests covering the new behavior.

At minimum:
- benchmark loading/regime-adapted wiring;
- provenance/status enforcement;
- session-aware cadence validation;
- OOS split behavior;
- canonical falsification report generation.

### CLI
A human should still be able to use the project through `run.ps1`.

Do not require undocumented sequences of Python commands.

### CI
Run:
- `pytest`
- `ruff check .`
- all relevant smoke/integration checks.

Do not claim completion if CI has not passed.

### Documentation
Update:
- `README.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/DECISIONS.md` when architectural/strategy decisions are made.

Keep `docs/AUDIT_20261002_POST_GEMINI.md` as the audit record; do not rewrite history to make previous findings disappear.

## 13. Final status rule

Until genuine historical data has been supplied and the required OOS research has actually run:

**ENGINE IMPLEMENTATION:** substantially complete  
**HISTORICAL STRATEGY RESEARCH:** not complete  
**OPTIONS RESEARCH:** unvalidated

Do not promote these statuses merely because fixtures pass.

## 14. Final response to the human

After implementation, report:

1. what changed;
2. tests/CI results;
3. remaining blockers;
4. exactly which parts are software validation versus genuine market evidence.

Do not report synthetic backtest performance as evidence of a trading edge.
