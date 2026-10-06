# Implementation Plan — High-Beta Tactical Research Engine

Status: ACTIVE — corrected after implementation audit on 2026-10-02.

This plan supersedes the earlier checklist. A phase is complete only when code, tests, documentation, the canonical runner, and CI agree.

## Research objective

Determine whether a deterministic approximation of the Reddit trader's observable behavior has positive expectancy after realistic execution costs, slippage, liquidity constraints, financing, leverage, and — only when historical option data exists — covered-call execution.

Always distinguish fixture validation from historical research. Synthetic fixtures prove that software works; they do not prove that the strategy works.

# Phase 0 — Stabilize the current scaffold [COMPLETED]

Build:
- [x] Keep run.ps1 as the canonical Windows entry point.
- [x] Keep run.bat as the double-click launcher.
- [x] Keep GitHub Actions CI as the automatic validation layer.
- [x] Ensure every user-facing CLI path has a smoke test.
- [x] Keep deterministic synthetic fixtures.

Tests:
- [x] deterministic fixture generation;
- [x] deterministic repeated backtests;
- [x] next-bar execution;
- [x] no-lookahead;
- [x] cost/slippage reconciliation;
- [x] multiple-symbol behavior.

Gate: pytest, fixture backtest, robustness smoke test, comparison smoke test, and CI must all pass. (PASSED)

# Phase 1 — Real historical equity-data ingestion [PARTIAL - BLOCKED ON REAL DATA]

Build a provider-independent data layer under src/tactical_engine/data/ for:
- [x] loading historical bars (CSV provider);
- [x] normalization and timezone handling;
- [x] OHLCV validation (monotonicity, duplicates, gaps, price anomalies);
- [x] provenance tracking;
- [x] source-data hashing (SHA-256 per file and aggregate universe digest);
- [x] validate declared bar resolution cadence (1m vs 1d spacing checks);
- [ ] ingest actual historical market data for MU, SNDK, SKHY, AMD, SMH, SPY, USD (currently uses synthetic sample data).

Initial configurable universe:
- [ ] MU (real market data)
- [ ] SNDK (real market data)
- [ ] SKHY (real market data)
- [ ] AMD (real market data)
- [ ] semiconductor benchmark (SMH)
- [ ] broad-market benchmark (SPY)
- [ ] verified 2× semiconductor ETF candidate (USD)

Required bar fields:
- [x] symbol;
- [x] timestamp;
- [x] OHLC;
- [x] volume;
- [x] source/provider;
- [x] adjustment status.

Explicitly handle and document splits, ticker changes, adjusted/unadjusted data, volume treatment, and delistings where relevant.

- [x] Add `.\run.ps1 doctor-data`: reports provider, symbols, date range, resolution, row counts, gaps, duplicates, timezone, OHLC/volume checks, corporate-action status, and data hash.
- [x] Add `.\run.ps1 historical`: refuses to run if required real-data inputs are missing. Persists provider/source, data hash, symbols, dates, resolution, timezone, adjustment policy, config hash, and git commit in `run_manifest.json`.

Gate: a real historical dataset passes validation and produces a reproducible equity-only backtest. (PENDING REAL DATASET)


# Phase 2 — Correct execution, accounting, and position mechanics [COMPLETED]

- [x] Fix execution order: signal timestamp -> order creation -> next eligible fill -> fill price -> costs -> portfolio state.
- [x] Default rule: a signal created at bar close may not fill on that same bar close (verified by test_no_lookahead.py).
- [x] Fix slippage double-count: execution price contains market slippage; cash uses execution price; trade P&L uses execution prices; commissions/fees are separate; slippage reported as attribution.
- [x] Add reconciliation tests (`tests/test_reconciliation.py`) tying starting equity, ending equity, realized P&L, unrealized P&L, fees, and financing together within tolerance.
- [x] Implement real liquidity behavior: oversized orders capped at 10% bar volume; never silently become full fills.
- [x] Support multiple positions, multiple entries, partial exits, average cost, realized/unrealized P&L, commissions, slippage, and financing.

# Phase 3 — Implement mechanics currently exposed only as configuration [COMPLETED]

- [x] Gross leverage actually constrains position sizing: `sum(abs(position_market_value)) <= equity * max_gross_leverage`.
- [x] Tested 1.0×, 1.25×, 1.5×, 2.0×, and 3.0× in `tests/test_phase3_mechanics.py`.
- [x] Symbol exposure strictly obeys: `position_value <= equity * max_symbol_weight`.
- [x] Risk sizing strictly obeys: `risk_budget = equity * risk_per_trade_pct / 100`, `quantity <= risk_budget / stop_distance`.
- [x] Implemented explicit layered-entry state (`LayerRecord`) tracking layer number, signal time, intended price, fill price, quantity, incremental risk, and aggregate risk.
- [x] Supported configured 1-, 2-, and 3-layer experiments without unbounded averaging down.
- [x] Implemented actual 2× ETF ingestion and trading (`USD.csv`) without synthetic return scaling.

# Phase 4 — Implement the actual signal feature set [COMPLETED]

Implement and test:
- [x] 1m, 5m, 15m, 1h, and 1d returns (`returns`, `ret_5`, `ret_15`, `ret_60`);
- [x] ATR and rolling volatility (`atr`, `rolling_vol`);
- [x] VWAP distance (`vwap_dist`);
- [x] pullback/displacement z-score (`zscore`);
- [x] trend slope (`trend_slope`);
- [x] relative volume (`rel_volume`);
- [x] time of day (`time_of_day_minute`);
- [x] distance from recent high/low (`dist_high`, `dist_low`);
- [x] event/earnings blackout state (`is_event_blackout`);
- [x] trend intact condition (`trend_ok`).

- [x] Maintain strict separation: raw bars -> features -> signal intent -> portfolio sizing -> order -> execution simulator. Signals do not mutate cash or positions.
- [x] Implemented and tested previously unused switches: `relative_volume_filter` (volume confirmation on pullbacks) and `event_filter` (suppressing entries during blackout periods) in `src/tactical_engine/signals/pullback.py` and `tests/test_features_and_filters.py`.

# Phase 5 — Real semiconductor sector/regime layer [COMPLETED]

Replaced single-symbol trend substitution with actual benchmark inputs and RegimeProvider architecture:
- [x] Configurable benchmark inputs: semiconductor sector benchmark (`SMH`) and broad-market benchmark (`SPY`).
- [x] Computed features: sector return, broad-market return, sector relative strength, sector trend, broad-market trend, and volatility regime.
- [x] Implemented `RegimeProvider` interface with:
  - `DefaultRegimeProvider`: Neutral baseline.
  - `BenchmarkRegimeProvider`: Genuine dual-benchmark tracking with configurable modes (`none`, `sector`, `broad`, `combined`).
  - `ExternalRegimeProvider`: Standalone CSV/JSON adapter compatible with optional RS2 / MRI / Macro Regime Identifier outputs.
- [x] Repository operates independently without requiring RS2.
- [x] Verified in `tests/test_regime_filtering.py`.

# Phase 6 — Historical options and covered-call engine [MECHANICALLY IMPLEMENTED / HISTORICALLY UNVALIDATED]

- [x] Hardened provider-neutral V2-D option quote models with executable bid/ask validation.
- [x] Added point-in-time option-chain lookup that never returns future quotes and enforces an explicit quote-freshness bound.
- [x] Added provider-neutral cbbo-1m normalization with exact timestamp-matched underlying prices.
- [x] Added V2-D option-data manifest/status validation and a gated manifest template.
- [x] Added explicit covered-call lifecycle state machine: AVAILABLE -> SOLD -> OPEN -> BOUGHT_BACK / EXPIRED / ASSIGNED.
- [x] Enforced covered-share capacity and bid-side sale / ask-side buyback accounting.
- [x] Rejected fabricated buyback prices when authentic option quotes are missing.
- [x] Added deterministic expiration/assignment cash and share-settlement tests.
- [ ] Ingest real historical option-chain dataset (currently UNVALIDATED due to absence of historical option chains).

# Phase 6 — Historical options and covered-call engine [MECHANICALLY IMPLEMENTED / HISTORICALLY UNVALIDATED]


- [x] OptionQuote model retaining underlying, contract ID, strike, expiration, timestamp, bid, ask, volume, open interest, and underlying price.
- [x] Do not substitute theoretical Black-Scholes prices for historical executable quotes. If real historical chains are unavailable, options experiment = UNVALIDATED.
- [x] Implement underlying ownership, call selection, realistic short fill, premium cash flow, repurchase variants (pullback, profit, expiration), assignment, expiration, and remaining underlying shares.
- [x] Implemented covered call repurchase variants: strength entry + pullback repurchase, strength entry + profit-based repurchase, hold to expiration.
- [x] Report option contribution separately from directional equity P&L (`options_premium_collected`, `options_realized_pnl`).
- [x] Verified in `tests/test_repurchase_covered_calls.py` and `tests/test_options_backtest.py`.
- [ ] Ingest real historical option-chain dataset (currently UNVALIDATED due to absence of historical option chains).

# Phase 7 — Realistic margin engine [COMPLETED]

- [x] Implement financing rate, buying power (`calculate_buying_power`), initial margin, maintenance margin, margin calls, forced liquidation, liquidation ordering, liquidation slippage, and residual debt (`calculate_residual_debt`).
- [x] Record peak gross exposure, peak debt, peak margin utilization, margin calls, forced liquidations, and worst liquidation event.
- [x] Added deterministic tests for buying power, margin calls, multi-position liquidation ordering, and residual debt in `tests/test_margin_risk.py`.

# Phase 8 — Canonical historical research runner [COMPLETED ENGINE LAYER]

- [x] Created `.\run.ps1 historical` Windows entry point.
- [x] Validates historical data and refuses execution if required real-data inputs are missing.
- [x] Loads frozen configuration and validates strategy inputs.
- [x] Generates machine-readable outputs (`run_manifest.json`, `metrics.json`, `trades.json`).
- [x] Generates Markdown reports with historical market data provenance banner.
- [x] Persists full run manifest (data hashes, config hash, git commit, symbols, timeframe).
- [x] Creates isolated result directory `reports/historical_<run_id>_<timestamp>/` that never overwrites prior runs.
- [x] Verify bar resolution cadence matching config resolution (1m vs 1d spacing checks).
- [x] Ensure default historical data directory exists on clean checkouts or defaults transparently to validated historical location.

# Phase 9 — Experiment matrix and anti-overfitting [COMPLETED ENGINE LAYER]

- [x] Strategy variants evaluated: `literal_clone`, `risk_controlled`, `regime_adapted`.
- [x] Leverage sensitivity tested: 1.0×, 1.25×, 1.5×, 2.0×, 3.0×.
- [x] Layering tested: 1, 2, 3 layers with explicit layer records and capacity limits.
- [x] Exit families: fixed percentage, ATR, VWAP reversion, time-based.
- [x] Cost sensitivity: 0 bps, 5 bps, 10 bps, 15 bps.
- [x] Robustness diagnostics: parameter perturbation sweeps, random-entry control, bootstrap resampling, and parameter stability scoring (0.0 to 1.0).
- [x] Implement stationary block bootstrap for autocorrelated intraday returns (`stationary_block_bootstrap`).
- [x] Implement ticker exclusion test (`run_ticker_exclusion_test`).
- [x] Implement strongest-day exclusion test (`run_strongest_day_exclusion_test`).

# Phase 10 — Historical reproduction of the Reddit-period behavior [ENGINE COMPLETE / RESEARCH BLOCKED ON REAL DATA]

- [x] Multi-variant comparison runner evaluates `literal_clone`, `risk_controlled`, and `regime_adapted` on identical fixture data.
- [x] Implemented canonical historical 3-variant comparison runner (`historical_comparison.py` and `.\run.ps1 comparison-historical`) operating on historical dataset.
- [ ] Execute reproduction on verified historical market data across Reddit period.
- [ ] Produce final historical comparison report (`reports/strategy_comparison_historical.md`).
- [x] Labels evidence strictly with `OBSERVED`, `DERIVED`, `HYPOTHESIS`, `ASSUMPTION`, and `UNVERIFIED`.
- [ ] Enforces falsification criteria: no edge declared without persistent out-of-sample positive expectancy after fees and financing.

# Hard blockers

Do not declare research-ready while any of these remain:
- only synthetic data is available;
- bar resolution cadence does not match declared configuration resolution;
- leverage is configuration-only;
- layering is configuration-only;
- 2× ETF support is configuration-only;
- regime filtering is only per-symbol trend;
- configured filters are unused;
- historical options are unavailable but option results are presented as validated;
- cost/slippage accounting is inconsistent;
- test data influenced parameter selection;
- provenance is incomplete;
- historical outputs can be silently overwritten;
- fixture output can be mistaken for historical research.

# Agent operating rules

1. Work one phase at a time.
2. Run tests after every phase.
3. Never silently change the strategy specification.
4. Record non-trivial decisions in docs/DECISIONS.md.
5. Update README.md whenever user-facing commands change.
6. Update this plan when phase status changes.
7. A phase is complete only when code + tests + documentation + CI agree.
8. Prefer a smaller correct implementation over a broad fake implementation.
9. If required data is unavailable, mark the phase BLOCKED or UNVALIDATED rather than fabricating data.
10. Never present a fixture result as evidence about the real strategy.

# Current status & Implementation Audit (Updated 2026-10-02 Post-Audit Pass)

Reference: `docs/execution_plan/PLAN.md`, `INSTRUCTIONS.md`, and `docs/AUDIT_20261002_POST_GEMINI.md`

**Status:**
- **ENGINE IMPLEMENTATION:** Complete and research-gate compliant.
- **HISTORICAL STRATEGY RESEARCH:** First canonical 3-variant comparison executed on verified 1-minute historical data (`massive_stocks_1m_51e9b529de55`).
- **OPTIONS RESEARCH:** Unvalidated (no historical tick-level option chains provided).
- **EVENT FILTERING:** Partial / Unvalidated (blackout logic active, but no historical earnings calendar feed connected).

### Closed Research Gates:
1. [x] **Authoritative Verified-Dataset Evidence Gate**: `assert_research_dataset_verified` strictly requires `REAL_HISTORICAL_VERIFIED` and `is_verified_market_data=True`. `run.ps1 historical` and `run.ps1 comparison-historical` refuse synthetic sample fixtures and unverified datasets with non-zero exit codes ($LASTEXITCODE != 0), and silent fixture fallbacks have been eliminated.
2. [x] **Tri-Partition Train / Validation / Test OOS Architecture**: `split_data_train_val_test` generates strictly disjoint partitions from `train_end`, `validation_end`, and `test_start`, producing separate metrics for all 3 strategy variants (`literal_clone`, `risk_controlled`, `regime_adapted`). Missing boundaries produce explicit unavailable status without fabrication.
3. [x] **Benchmark vs. Strategy Robustness Diagnostics & Complete Session Time Axis**: Clear separation between `Benchmark Return Dependence Diagnostic` (`resampling_unit: benchmark_bar_returns`) and `Strategy-Level Return Robustness Diagnostic` (`resampling_unit: strategy_daily_returns`). Strategy bootstrap preserves the complete daily trading session axis (active realized P&L + zero-return inactive sessions) over the evaluation period. Diagnostic scopes (`FULL`, `TEST_OOS`) and observation definitions are explicitly reported. Undersized samples (< 10 sessions or < 10 active days) explicitly render `INSUFFICIENT_SAMPLE`.
4. [x] **Benchmark Decoupling & Regime Wiring**: `SMH` and `SPY` automatically loaded into `regime_adapted` while tradable universe execution is restricted to tradable symbols. `literal_clone` and `risk_controlled` remain unaffected when `sector_filter` is disabled.
5. [x] **Session-Aware Cadence Validation**: Distinguishes intraday 1m spacing from legitimate overnight/weekend/holiday gaps while strictly rejecting cadence mismatches.
6. [x] **Reconciled Experiment Grids**: Leverage sensitivities tested at `[1.0, 1.25, 1.5, 2.0, 3.0]` and cost sensitivities at `[0.0, 5.0, 10.0, 15.0]` bps.
7. [x] **Genuine Market Data Ingestion Pipeline**: Ingested 1-minute historical aggregate bars for `MU`, `SNDK`, `SKHY`, `AMD`, `USD`, `SMH`, and `SPY` via Massive Stocks REST API for the 2026-07-01 to 2026-09-30 observation window. Filtered strictly to U.S. regular trading hours, validated via `doctor-data`, and generated authoritative manifest `massive_stocks_1m_51e9b529de55.json`.
8. [x] **Canonical 3-Variant Historical Comparison Execution**: Executed `run.ps1 comparison-historical` on verified 1-minute data across 175,000+ bars with $O(1)$ event loop optimizations, generating machine-readable JSON metrics and Markdown reports.
9. [x] **Post-First-Real-Run Audit & ATR Exit Geometry Freeze**: Stored stop/target/entry ATR at entry to prevent volatility expansion/contraction exit drift; added full trade-frequency and cost decomposition diagnostics; froze explicit chronological train/val/test partitions (`2026-07-01` -> `2026-08-15` -> `2026-09-01` -> `2026-09-30`) in `configs/historical_1m.yaml`; verified full test suite passes with clean Git hash.

### Remaining Research Blockers:
1. [ ] **Genuine Option Chain Ingestion**: Ingest historical tick-level option quotes before removing `UNVALIDATED` flag from covered-call experiments.
2. [ ] **Event Calendar Data**: Connect verified historical earnings calendar feed to validate event blackout mechanisms.


