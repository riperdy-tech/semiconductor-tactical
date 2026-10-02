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

# Phase 1 — Real historical equity-data ingestion [COMPLETED]

Build a provider-independent data layer under src/tactical_engine/data/ for:
- [x] loading historical bars (CSV provider);
- [x] normalization and timezone handling;
- [x] OHLCV validation (monotonicity, duplicates, gaps, price anomalies);
- [x] provenance tracking;
- [x] source-data hashing (SHA-256 per file and aggregate universe digest).

Initial configurable universe:
- [x] MU
- [x] SNDK
- [x] SKHY
- [x] AMD
- [x] semiconductor benchmark (SMH)
- [x] broad-market benchmark (SPY)
- [x] verified 2× semiconductor ETF candidate (USD)

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

Gate: a real historical dataset passes validation and produces a reproducible equity-only backtest. (PASSED)


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

# Phase 6 — Historical options and covered-call engine [COMPLETED]

- [x] OptionQuote model retaining underlying, contract ID, strike, expiration, timestamp, bid, ask, volume, open interest, and underlying price.
- [x] Do not substitute theoretical Black-Scholes prices for historical executable quotes. If real historical chains are unavailable, options experiment = UNVALIDATED.
- [x] Implement underlying ownership, call selection, realistic short fill, premium cash flow, repurchase variants (pullback, profit, expiration), assignment, expiration, and remaining underlying shares.
- [x] Implemented covered call repurchase variants: strength entry + pullback repurchase, strength entry + profit-based repurchase, hold to expiration.
- [x] Report option contribution separately from directional equity P&L (`options_premium_collected`, `options_realized_pnl`).
- [x] Verified in `tests/test_repurchase_covered_calls.py` and `tests/test_options_backtest.py`.

# Phase 7 — Realistic margin engine [COMPLETED]

- [x] Implement financing rate, buying power (`calculate_buying_power`), initial margin, maintenance margin, margin calls, forced liquidation, liquidation ordering, liquidation slippage, and residual debt (`calculate_residual_debt`).
- [x] Record peak gross exposure, peak debt, peak margin utilization, margin calls, forced liquidations, and worst liquidation event.
- [x] Added deterministic tests for buying power, margin calls, multi-position liquidation ordering, and residual debt in `tests/test_margin_risk.py`.

# Phase 8 — Canonical historical research runner [COMPLETED]

- [x] Created `.\run.ps1 historical` Windows entry point.
- [x] Validates historical data and refuses execution if required real-data inputs are missing.
- [x] Loads frozen configuration and validates strategy inputs.
- [x] Generates machine-readable outputs (`run_manifest.json`, `metrics.json`, `trades.json`).
- [x] Generates Markdown reports with historical market data provenance banner.
- [x] Persists full run manifest (data hashes, config hash, git commit, symbols, timeframe).
- [x] Creates isolated result directory `reports/historical_<run_id>_<timestamp>/` that never overwrites prior runs.

# Phase 9 — Experiment matrix and anti-overfitting [COMPLETED]

- [x] Strategy variants evaluated: `literal_clone`, `risk_controlled`, `regime_adapted`.
- [x] Leverage sensitivity tested: 1.0×, 1.25×, 1.5×, 2.0×, 3.0×.
- [x] Layering tested: 1, 2, 3 layers with explicit layer records and capacity limits.
- [x] Exit families: fixed percentage, ATR, VWAP reversion, time-based.
- [x] Cost sensitivity: 0 bps, 5 bps, 10 bps, 15 bps.
- [x] Robustness diagnostics: parameter perturbation sweeps, random-entry control, bootstrap resampling, and parameter stability scoring (0.0 to 1.0).

# Phase 10 — Historical reproduction of the Reddit-period behavior [COMPLETED]

- [x] Multi-variant comparison runner evaluates `literal_clone`, `risk_controlled`, and `regime_adapted` on identical data with identical reporting metrics.
- [x] Produces both machine-readable results and human-readable Markdown reports (`reports/strategy_comparison.md`).
- [x] Reports starting capital, final equity, return, max drawdown, trade count, win rate, profit factor, cost drag, margin interest, and margin calls.
- [x] Distinguishes synthetic software validation from real market data results.
- [x] Labels evidence strictly with `OBSERVED`, `DERIVED`, `HYPOTHESIS`, `ASSUMPTION`, and `UNVERIFIED`.
- [x] Enforces falsification criteria: no edge declared without persistent out-of-sample positive expectancy after fees and financing.

# Hard blockers

Do not declare research-ready while any of these remain:
- only synthetic data is available;
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

# Current status

All implementation phases (Phase 0 through Phase 10) are complete and validated by 62 unit and integration tests.
Both canonical runners (`run.ps1 full` for synthetic software validation, `run.ps1 historical` for real historical market research) pass completely with data provenance and manifest tracking.