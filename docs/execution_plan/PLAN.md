# Execution Plan — Remaining Research-Integrity Pass

## Phase 1 — Enforce the real-data evidence gate

### Problem

The repository now has an explicit `DatasetManifest`, but an unverified dataset can still proceed through the historical runners with only a warning. The report path can also describe an unverified dataset as real historical data.

### Required implementation

Create one authoritative gate, preferably a pure function such as:

`assert_research_dataset_verified(dataset_manifest, config)`

It must reject:

- `SYNTHETIC_SAMPLE_FIXTURE`;
- `REAL_HISTORICAL_UNVERIFIED_SOURCE`;
- missing manifest;
- `REAL_HISTORICAL_VERIFIED` with `is_verified_market_data != true`;
- manifest bar resolution that conflicts with the loaded configuration;
- missing source/provenance fields required by `DATA_CONTRACT.md`.

### Runner behavior

`run_historical_backtest` and `run_historical_comparison` must:

- refuse the research-evidence path unless the dataset is `REAL_HISTORICAL_VERIFIED`;
- allow a clearly separated fixture-validation path for synthetic data;
- never print `REAL HISTORICAL MARKET DATA` for an unverified source;
- include dataset status in the manifest and report;
- preserve fixture warnings.

Do not infer verification from directory names.

### CLI requirement

`run.ps1 historical` and `run.ps1 comparison-historical` must have deterministic behavior:

- genuine verified dataset -> execute;
- unverified local CSV dataset -> refuse research execution;
- synthetic fixture -> refuse research execution with an explicit fixture message.

Do not silently fall back from `data/processed` to synthetic data for historical research commands.

A separate fixture command may continue to use `data/sample_historical`.

---

## Phase 2 — Build real train / validation / test OOS evaluation

### Problem

The current OOS infrastructure is effectively a single in-sample/out-of-sample split.

### Required implementation

Use the existing `ResearchConfig` fields:

- `start`
- `end`
- `train_end`
- `validation_end`
- `test_start`

Create an explicit split representation:

- `train`
- `validation`
- `test`

Do not silently collapse the validation period into the training period.

### Variant coverage

For each of:

- `literal_clone`
- `risk_controlled`
- `regime_adapted`

produce metrics for:

- train;
- validation;
- final test/OOS.

The final test period must be isolated from parameter selection.

### Research integrity

If a date boundary is missing, do not fabricate one.

The report must say OOS evaluation is unavailable rather than manufacturing a split.

If `test_start` exists, it must define the untouched final test segment.

If `train_end` and `validation_end` exist, use them explicitly.

---

## Phase 3 — Separate benchmark diagnostics from strategy robustness

### Current ambiguity

The stationary block bootstrap currently operates on benchmark/universe price returns.

That is useful, but it is not the same as bootstrapping the strategy's realized P&L.

### Required implementation

Keep the benchmark-return bootstrap, but rename/document it as:

**Benchmark Return Dependence Diagnostic**

Then add a distinct strategy-level robustness diagnostic that operates on strategy outcomes.

The implementation may use:

- trade-level returns when trades are non-overlapping and that limitation is explicitly documented;
- daily strategy P&L/equity returns where available;
- another method justified by `BACKTEST_PROTOCOL.md`.

Do not pretend ordinary iid trade resampling preserves intraday autocorrelation.

### Output labels

Every diagnostic must state what is being resampled:

- market/benchmark returns;
- strategy daily returns;
- trade outcomes;
- or another explicit object.

---

## Phase 4 — Run falsification on the final OOS experiment

### Required architecture

The canonical research pipeline should conceptually be:

```
verified historical dataset
        |
        v
train / validation / test split
        |
        +--> literal_clone
        +--> risk_controlled
        +--> regime_adapted
        |
        v
final test/OOS results
        |
        +--> ticker exclusion
        +--> strongest-day diagnostic
        +--> strategy-level bootstrap
        +--> cost sensitivity
        +--> leverage sensitivity
        +--> parameter perturbation
        +--> random-entry control
        +--> regime decomposition
        |
        v
final research report
```

The falsification analysis must not silently substitute full-sample results for the untouched test period.

If a diagnostic is not statistically meaningful on the test sample because the sample is too small, report that limitation rather than forcing a score.

---

## Phase 5 — Report evidence classes correctly

The final Markdown report must distinguish:

### Software validation

Examples:

- tests passed;
- accounting reconciles;
- no-lookahead tests pass;
- cadence validator rejects bad input;
- manifest gate refuses unverified data.

### Market evidence

Only available after genuine verified market data is supplied and run:

- historical returns;
- drawdowns;
- trade statistics;
- OOS performance;
- robustness outcomes.

### Unvalidated components

Keep:

- covered calls = `UNVALIDATED`;
- event/earnings filter = `PARTIAL / UNVALIDATED`

until their actual data contracts are satisfied.

---

## Phase 6 — Reconcile CLI behavior and documentation

Update:

- `README.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/DECISIONS.md` for architectural decisions.

Ensure these statements are literally true:

- historical research refuses synthetic/unverified data;
- comparison-historical cannot silently downgrade to fixtures;
- OOS is train/validation/test;
- three strategy variants are evaluated separately on the same split;
- robustness diagnostics identify their underlying resampling object.

No documentation should claim research completion.

---

## Phase 7 — Do not cross the data/optimization boundary

Do **not**:

- acquire real market data;
- scrape Reddit again;
- invent option chains;
- invent earnings events;
- change strategy thresholds because of performance;
- optimize parameters against the final test period;
- report fixture returns as market evidence.

This pass ends with a **research-ready engine**, not a research result.
