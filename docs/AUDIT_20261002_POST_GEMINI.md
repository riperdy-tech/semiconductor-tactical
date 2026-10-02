# Post-Gemini Implementation Audit — 2026-10-02

## Verdict

The Gemini implementation is substantially better than the original scaffold: the core execution/accounting, sizing, layering, regime, margin, and covered-call machinery now exist, and GitHub Actions is green on Windows/Ubuntu with Python 3.11/3.12.

However, the repository is **not yet research-ready for the original Reddit-strategy question**.

The central problem is that the checked-in historical dataset is synthetic. Several documents currently mark Phases 1–10 complete even though the real-data and out-of-sample research gates have not been satisfied.

## Findings

### P1 — `data/sample_historical` is synthetic, not real market data

`scripts/generate_sample_historical.py` explicitly generates deterministic pseudo-random prices and writes them into `data/sample_historical`.

The generated MU dataset contains exactly 250 daily rows from 2014-01-02 through 2014-12-17.

That means the historical runner can exercise the ingestion/backtest code, but it does **not** provide evidence from actual historical MU/SNDK/SKHY/AMD/SMH/SPY/USD market prices.

**Status:** BLOCKED

### P2 — The default historical runner points to a non-checked-in directory

`run.ps1` defaults to `data/processed`, but the repository tree contains only `data/sample_historical`; `data/processed` is ignored by git.

Therefore a clean checkout does not have the default historical data required by `.un.ps1 historical`.

**Status:** BLOCKED

### P3 — Bundled sample data is daily while the strategy is configured for 1-minute bars

`configs/base.yaml` sets `strategy.bar_interval: 1m`.

The bundled sample data is daily.

The loader records the configured resolution but does not verify that observed timestamp cadence matches the declared resolution.

This matters because the strategy uses 5-minute, 15-minute, 60-minute features and a 120-minute maximum holding period.

Running daily data through a nominal 1m configuration is not an intraday tactical backtest.

**Status:** BLOCKED

### P4 — Phase 10 is not an actual historical reproduction

The historical runner executes one loaded configuration through `run_backtest()`.

The multi-variant comparison CLI still generates synthetic bars.

So the repo can compare variants on fixtures, and it can run one configuration on the sample dataset, but there is not yet a canonical command that runs literal_clone, risk_controlled, and regime_adapted on the same real historical dataset and produces the final comparison required by the plan.

**Status:** BLOCKED

### P5 — Phase 9 robustness matrix is incomplete

The plan required ticker exclusion, strongest-day exclusion, randomized entry timing, block bootstrap, regime-by-regime decomposition, leverage sensitivity, cost sensitivity, and parameter perturbation.

The current documented implementation covers parameter perturbation, random-entry control, bootstrap resampling, and a stability score, but the full falsification matrix is not implemented as specified.

In particular, a simple bootstrap of trade outcomes is not equivalent to a block bootstrap for autocorrelated intraday returns.

**Status:** PARTIAL

### P6 — Covered-call mechanics exist, but no real historical option-chain dataset exists

The code now has repurchase logic, assignment logic, and option attribution.

The tests use generated quote fixtures.

No real historical option-chain dataset is present in the repository.

Therefore the option engine is mechanically implemented but historically `UNVALIDATED`.

**Status:** PARTIAL / UNVALIDATED

### P7 — Event filter is structurally implemented but currently defaults to no event

`compute_bar_features()` sets `is_event_blackout = False`.

There is currently no event/earnings data wired into the standard historical runner.

So the switch exists, but it does not currently protect the real historical strategy from earnings/events.

**Status:** PARTIAL

### P8 — Data validation does not validate declared timeframe cadence

The validator detects large calendar gaps and duplicate timestamps, but it does not verify expected 1-minute spacing for a 1m configuration, expected daily spacing for a 1d configuration, or regular-session calendar correctness.

Therefore a daily dataset can pass under a nominal 1m configuration.

**Status:** NEEDS FIX

## What is genuinely improved

The following implementation work appears to be real and is supported by code/tests:

- gross leverage constraint in position sizing;
- layered-entry state;
- 2× ETF instrument handling;
- multi-horizon feature calculations;
- relative-volume filter;
- benchmark-based regime provider;
- external regime adapter;
- covered-call repurchase mechanics;
- margin/buying-power/forced-liquidation components;
- slippage/accounting reconciliation;
- next-bar execution tests.

GitHub Actions run #12 is green across all four configured OS/Python combinations.

## Research readiness

Current recommended labels:

**ENGINE IMPLEMENTATION: substantially complete**

**HISTORICAL STRATEGY RESEARCH: not yet complete**

That distinction matters. The code is now much closer to a real research engine, but the evidence pipeline still lacks real intraday market data and a valid historical comparison experiment.

## Required next sequence

1. Replace the generated sample dataset with actual historical data.
2. Verify actual bar resolution and enforce it in validation.
3. Create a dedicated historical research config for real 1-minute data.
4. Add a canonical historical three-variant comparison runner using the same real dataset.
5. Complete the missing falsification tests.
6. Keep covered-call results explicitly UNVALIDATED until real historical option chains are supplied.
7. Only then evaluate the Reddit-period reproduction.

Do not optimize strategy parameters or draw conclusions from the current `data/sample_historical` results.