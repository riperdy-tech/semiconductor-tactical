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

# Phase 4 — Implement the actual signal feature set

Implement and test:
- 1m, 5m, 15m, 1h, and 1d returns;
- ATR and rolling volatility;
- VWAP distance;
- pullback/displacement z-score;
- trend slope;
- relative volume;
- time of day;
- distance from recent high/low;
- sector-relative return;
- cross-sectional relative strength;
- event/earnings blackout state where real data exists.

These are hypotheses for mechanically approximating discretionary chart reading, not claims about the Reddit trader's exact algorithm.

Maintain this separation:
raw bars -> features -> signal intent -> portfolio sizing -> order -> execution simulator

Signals must not directly mutate cash or positions.

Either implement currently unused switches such as relative_volume_filter and event_filter with tests, or remove them with a documented decision.

# Phase 5 — Real semiconductor sector/regime layer

The current regime_adapted implementation substitutes a symbol's own trend for a sector regime. Replace that with actual configurable benchmark inputs.

Minimum inputs:
- semiconductor sector benchmark;
- broad market benchmark;
- volatility/risk proxy where available.

Compute:
- sector return;
- broad-market return;
- sector relative strength;
- sector trend;
- broad-market trend;
- volatility regime.

Create an optional RegimeProvider interface with neutral/default, CSV/JSON, and optional RS2/MRI adapters.

This repository must remain runnable without RS2.

Compare no filter, sector filter, broad-market filter, and combined filter. Do not claim superiority from one in-sample result.

# Phase 6 — Historical options and covered-call engine

Begin only after the equity engine is historically valid.

Historical option data must retain underlying, contract ID, strike, expiration, timestamp, bid, ask, volume, open interest, and underlying price.

Do not substitute theoretical Black-Scholes prices for historical executable quotes.

If real historical chains are unavailable:
    options experiment = UNVALIDATED

and continue equity-only research independently.

Implement underlying ownership, call selection, realistic short fill, premium cash flow, pullback repurchase, time/profit repurchase variants, assignment, expiration, early exercise where supported, and remaining underlying shares.

Required option variants:
- strength entry + pullback repurchase;
- strength entry + profit-based repurchase;
- hold to expiration.

Report option contribution separately from directional equity P&L.

# Phase 7 — Realistic margin engine

Implement financing rate, buying power, initial margin, maintenance margin, relevant intraday/overnight constraints, margin calls, forced liquidation, liquidation ordering, liquidation slippage, and residual debt.

Record peak gross exposure, peak debt, peak margin utilization, margin calls, forced liquidations, and worst liquidation event.

Add deterministic tests for no-call, call, multi-position liquidation, liquidation slippage, and residual debt.

# Phase 8 — Canonical historical research runner

Create:
    .\run.ps1 historical

It must:
1. validate historical data;
2. load a frozen configuration;
3. validate strategy inputs;
4. run the requested strategy;
5. run robustness checks;
6. generate machine-readable outputs;
7. generate Markdown reports;
8. write a run manifest;
9. create a unique result directory;
10. never silently overwrite a prior run.

Suggested output:
reports/<run_id>/run_manifest.json
reports/<run_id>/metrics.json
reports/<run_id>/trades.parquet
reports/<run_id>/equity_curve.parquet
reports/<run_id>/parameter_sweep.csv
reports/<run_id>/report.md

# Phase 9 — Experiment matrix and anti-overfitting

Strategy variants:
- literal_clone;
- risk_controlled;
- regime_adapted.

Leverage:
- 1.0×;
- 1.25×;
- 1.5×;
- 2.0×;
- 3.0×.

Layering:
- 1;
- 2;
- 3.

Exit families:
- fixed percentage;
- ATR;
- VWAP reversion;
- time-based;
- trailing.

Cost sensitivity:
- 0 bps;
- 5 bps;
- 10 bps;
- 15 bps;
- source-specific spread assumptions when available.

Robustness tests:
- parameter perturbation;
- ticker exclusion;
- strongest-day exclusion;
- random-entry control;
- randomized entry timing;
- trade-order bootstrap;
- block bootstrap;
- regime decomposition;
- leverage sensitivity;
- cost sensitivity.

Use genuine training, validation, and untouched test periods. Parameters may be selected only from training/validation.

Do not report only the best parameter set. Report neighborhood performance, median/dispersion, positive-expectancy coverage, drawdown coverage, and out-of-sample persistence.

# Phase 10 — Historical reproduction of the Reddit-period behavior

Only after Phases 1–9 are valid.

Evaluate:
- literal_clone: closest feasible deterministic approximation;
- risk_controlled: same signal family with explicit risk/exposure limits;
- regime_adapted: risk-controlled plus actual sector/market regime data.

For each report starting capital, final equity, return, max drawdown, trade count, turnover, gross/net P&L, transaction costs, financing, leverage, margin utilization, margin calls, ticker attribution, date concentration, and out-of-sample status.

Do not optimize directly for the Reddit author's reported dollar result.

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

# Current priority

Next: Phase 0 completion, then Phase 1 historical equity-data ingestion.
Do not optimize strategy thresholds, leverage, covered calls, or headline returns until real historical equity data and correct accounting are in place.