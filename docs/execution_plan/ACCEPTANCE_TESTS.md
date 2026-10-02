# Acceptance Tests — Research-Integrity Pass

## A. Dataset verification gate

### A1 — Synthetic fixture refusal

Given:

`data/sample_historical/dataset_manifest.json`

with:

`data_status = SYNTHETIC_SAMPLE_FIXTURE`

then:

- `run.ps1 historical` must refuse the research-evidence path;
- `run.ps1 comparison-historical` must refuse the research-evidence path;
- the console/report must explicitly say the dataset is synthetic.

### A2 — Unverified-source refusal

Given a directory containing valid CSV files but no manifest, both historical research runners must refuse execution.

Expected classification:

`REAL_HISTORICAL_UNVERIFIED_SOURCE`

not real research.

### A3 — Verified-source acceptance

Given a fixture-style test dataset whose manifest explicitly says:

`REAL_HISTORICAL_VERIFIED`

and `is_verified_market_data=true`, and whose cadence/provenance contract is valid, the research runner may proceed.

This test must use deterministic test data only; it is a gate test, not market evidence.

### A4 — No path-name spoofing

Renaming a synthetic directory must not change its research status.

---

## B. Train / validation / test split

### B1

Given explicit:

- `train_end`
- `validation_end`
- `test_start`

produce separate train, validation, and test datasets.

### B2

No timestamp may appear in more than one split.

### B3

The final test dataset must start at or after `test_start`.

### B4

Each of the 3 strategy variants must produce:

- train metrics;
- validation metrics;
- test metrics.

### B5

Missing OOS boundaries must produce an explicit unavailable status, not a fabricated split.

---

## C. Regime-adapted isolation

Retain existing benchmark wiring tests and ensure:

- SMH/SPY are loaded;
- they are not tradable unless explicitly configured;
- `regime_adapted` can respond to benchmark regime;
- `literal_clone` and `risk_controlled` remain independent when `sector_filter=false`.

---

## D. Robustness diagnostics

### D1 — Benchmark diagnostic

The existing stationary bootstrap must be clearly identified as a benchmark/market-return diagnostic.

### D2 — Strategy diagnostic

Add a separate strategy-outcome bootstrap or equivalent strategy-level robustness test.

The report must identify its resampling unit.

### D3 — Ticker exclusion

Leave-one-out analysis must be tied to the named strategy variant and period under study.

### D4 — Strongest-day exclusion

Keep the current “attribution diagnostic” wording unless the strategy is actually re-run with those days removed.

### D5 — Final OOS linkage

The canonical final research report must be able to render robustness results for the final test/OOS period.

If the sample is insufficient, render `INSUFFICIENT_SAMPLE` rather than a misleading numeric conclusion.

---

## E. Experiment matrix consistency

The code and documentation must agree on:

### Leverage

- 1.0x
- 1.25x
- 1.5x
- 2.0x
- 3.0x

### Cost sensitivity

- 0 bps
- 5 bps
- 10 bps
- 15 bps

---

## F. Evidence classification

Reports must not contain any path where:

`REAL_HISTORICAL_UNVERIFIED_SOURCE`

is rendered as:

`REAL HISTORICAL MARKET DATA`

The report must explicitly distinguish:

- software validation;
- unverified historical inputs;
- verified historical market evidence.

---

## G. CLI / CI

Run and pass:

```powershell
.un.ps1 doctor
.un.ps1 doctor-data
.un.ps1 test
.un.ps1 historical
.un.ps1 comparison-historical
```

with the documented expectation that the last two **refuse** the bundled synthetic/unverified dataset.

Also pass:

```text
python -m pytest
python -m ruff check .
```

CI must pass.

---

## H. Final status

Only after all tests above pass may the implementation be described as:

**ENGINE IMPLEMENTATION: substantially complete and research-gate compliant**

The repository must still state:

**HISTORICAL STRATEGY RESEARCH: not complete — genuine verified market data required**

**OPTIONS RESEARCH: unvalidated**

**EVENT FILTERING: partial / unvalidated**
