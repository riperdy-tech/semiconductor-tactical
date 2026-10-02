# Decisions

## 2026-10-02 — New repository boundary

**Decision:** Create a separate repo instead of extending RS2.

**Reason:** The target strategy is tactical/high-turnover and primarily market-microstructure/price-action driven. RS2 is an equity-analysis/valuation engine. Coupling them would blur test boundaries.

**Integration:** Optional RS2 regime adapter only.

## 2026-10-02 — Deterministic core

**Decision:** No LLM in signal generation or backtest accounting.

**Reason:** We need reproducibility and falsifiability. LLMs may later be used for research summarization, but not to decide simulated orders in the first version.

## 2026-10-02 — Separate literal vs risk-controlled modes

**Decision:** Preserve the source behavior as an experiment rather than silently "fixing" it.

**Reason:** If we only build a safer strategy, we cannot determine which part of the reported result came from leverage/layering versus the underlying signal.

## 2026-10-02 — Slippage and execution accounting separation

**Decision:** Market slippage is incorporated directly into the fill price (`fill.price = intended_price +/- slippage`), and trade P&L is calculated strictly using actual execution prices minus commissions. Slippage is tracked as an attribution metric rather than being deducted twice.

**Reason:** Resolves audit finding C8 where slippage was double-counted against realized P&L. Ensures exact $0.01 mathematical reconciliation between cash flow and portfolio equity.

## 2026-10-02 — Gross leverage constraint in portfolio sizing

**Decision:** Enforce `max_gross_leverage` directly at position sizing time by calculating active aggregate market value of all holdings and capping new orders by remaining gross leverage capacity.

**Reason:** Resolves audit finding C2 where leverage was a dormant configuration parameter. Prevents gross portfolio exposure from exceeding defined risk bounds regardless of symbol count.

## 2026-10-02 — Dual-benchmark regime tracking

**Decision:** Use `BenchmarkRegimeProvider` consuming both semiconductor sector (`SMH`) and broad market (`SPY`) historical series, with configurable regime filter modes (`none`, `sector`, `broad`, `combined`), and provide an optional `ExternalRegimeProvider` for external format compatibility.

**Reason:** Resolves audit finding C5 where single-ticker trend was substituted for genuine sector and broad-market regime evaluation. Keeps the engine completely self-contained.

## 2026-10-02 — Covered-call repurchase mechanics and option attribution

**Decision:** Implement explicit covered-call repurchase rules (`pullback`, `profit_target_50pct`, `expiration`) and segregate option cash flows (`options_premium_collected`, `options_realized_pnl`) from directional equity P&L. Default option simulations to `UNVALIDATED` unless backed by primary historical chain quotes.

**Reason:** Resolves audit finding C7 by accurately modeling the observed Reddit trader behavior (harvesting premium on strength and buying back on pullbacks) while upholding data integrity rules in `AGENTS.md`.

## 2026-10-02 — Benchmark decoupling and regime-adapted wiring

**Decision:** Automatically load sector (`SMH`) and broad-market (`SPY`) benchmarks in the historical comparison engine to feed `BenchmarkRegimeProvider`, while explicitly filtering `tradable_symbols` during portfolio execution. In `pullback.py`, `regime_allows` is strictly bypassed unless `config.sector_filter` is enabled.

**Reason:** Resolves requirement in `INSTRUCTIONS.md`. Guarantees that `regime_adapted` operates with genuine benchmark market inputs, while ensuring the engine never erroneously trades benchmark ETFs and ensuring `literal_clone` and `risk_controlled` remain unaffected by benchmark regime state.

## 2026-10-02 — Explicit dataset manifest provenance contract

**Decision:** Implement `dataset_manifest.json` (`DatasetManifest` model) with strict status enumeration (`SYNTHETIC_SAMPLE_FIXTURE`, `REAL_HISTORICAL_UNVERIFIED_SOURCE`, `REAL_HISTORICAL_VERIFIED`). Never infer real historical research status from directory names alone.

**Reason:** Resolves requirement in `INSTRUCTIONS.md` preventing accidental or spoofed promotion of synthetic fixtures to real historical research.

## 2026-10-02 — Session-aware bar cadence validation

**Decision:** Compute bar timestamp deltas exclusively between consecutive bars sharing the same calendar date (`prev.date == curr.date`).

**Reason:** Resolves requirement in `INSTRUCTIONS.md` to prevent legitimate overnight, weekend, and holiday gaps from failing 1-minute intraday cadence checks, while preserving strict rejection of mismatched data (e.g. daily data supplied to a 1-minute engine).

## 2026-10-02 — Integration of falsification suite into canonical report

**Decision:** Execute stationary block bootstrap (500 iterations), leave-one-out ticker exclusion, and strongest-day exclusion diagnostics directly in `run_strategy_comparison` and render them in the canonical Markdown/JSON output.

**Reason:** Resolves requirement in `INSTRUCTIONS.md` ensuring falsification tests are part of the canonical research workflow rather than uninvoked helper utilities.

## 2026-10-02 — Authoritative verified-dataset evidence gate

**Decision:** Implement `assert_research_dataset_verified` to strictly enforce `REAL_HISTORICAL_VERIFIED` with `is_verified_market_data=True` before historical research runners execute. Make `run.ps1 historical` and `run.ps1 comparison-historical` refuse unverified and synthetic datasets with explicit refusal notices, while eliminating silent fallbacks to sample fixtures.

**Reason:** Resolves Gate A from `docs/execution_plan/PLAN.md` preventing unverified local files or synthetic fixtures from entering research-evidence pipelines.

## 2026-10-02 — Tri-partition train / validation / test OOS architecture

**Decision:** Implement `split_data_train_val_test` partitioning data into strictly pairwise-disjoint sets using explicit `train_end`, `validation_end`, and `test_start` boundaries, and evaluate all three canonical variants (`literal_clone`, `risk_controlled`, `regime_adapted`) across all three partitions.

**Reason:** Resolves Gate B from `docs/execution_plan/PLAN.md`, preventing parameter tuning from contaminating the untouched final test segment and avoiding the collapse of validation into training.

## 2026-10-02 — Benchmark vs strategy-level robustness separation

**Decision:** Formally separate market return diagnostics from strategy robustness diagnostics. Stationary block bootstrap on price returns is labeled `Benchmark Return Dependence Diagnostic` (`resampling_unit: benchmark_bar_returns`), while `Strategy-Level Return Robustness Diagnostic` resamples daily realized net returns (`resampling_unit: strategy_daily_returns`). Samples with fewer than 10 observations (including small OOS samples) explicitly withhold estimates and render `INSUFFICIENT_SAMPLE`.

**Reason:** Resolves Gate D from `docs/execution_plan/PLAN.md` to prevent conflating benchmark return properties with strategy execution robustness.

## 2026-10-02 — Final integrity gate fixes: CLI non-zero refusal, complete daily bootstrap session axis, and explicit diagnostic scopes

**Decision:**
1. **CLI Non-Zero Exit Code on Refusal:** Updated CLI `main()` in `tactical_engine.historical_runner` and `tactical_engine.research.historical_comparison` to raise and exit with status code 1 upon `DatasetVerificationError`. Verified that `.\run.ps1 historical` and `.\run.ps1 comparison-historical` fail and exit with non-zero `$LASTEXITCODE` on unverified/synthetic data.
2. **Complete Daily Session Time Axis:** Refined `strategy_return_bootstrap` to preserve the complete daily trading session axis (active realized P&L + zero-return inactive sessions) over the evaluation period rather than omitting non-trading sessions. Added explicit observation definition and active/inactive session counting.
3. **Explicit Diagnostic Scopes:** Tagged all robustness diagnostics with explicit period scopes (`FULL`, `TRAIN`, `VALIDATION`, `TEST_OOS`) in data models and reports, and documented that leave-one-out ticker exclusion and strongest-day exclusion tests are intentionally full-sample diagnostics.

**Reason:** Resolves all requirements in `docs/execution_plan/FINAL_GATE_FIX.md` and fulfills the handoff contract in `docs/execution_plan/GEMINI_FINAL_HANDOFF.md`.

## 2026-10-02 — Massive 1-minute historical market data ingestion pipeline

**Decision:**
1. **Pipeline Architecture:** Implemented `tactical_engine.data.massive` downloading 1-minute custom aggregate bars from Massive Stocks REST endpoint (`/v2/aggs/ticker/{ticker}/range/1/minute/{from}/{to}`) for the required 7-symbol universe (`MU`, `SNDK`, `SKHY`, `AMD`, `USD`, `SMH`, `SPY`).
2. **Session & Timezone Standards:** Converted Unix ms timestamps to `America/New_York` to filter strictly to U.S. regular trading hours (09:30:00 to 15:59:59 ET, Mon–Fri), and serialized to UTC ISO-8601 timestamps. Preserved market gaps without fabricating or forward-filling synthetic bars.
3. **Audit Manifest Schema:** Implemented dataset manifest adhering to `MASSIVE_DATA_MANIFEST_SCHEMA.md` with SHA-256 hashes per symbol, aggregate hash, coverage diagnostics, and instrument history caveats (`SKHY` Nasdaq ADR listing 2026-07-10, `SNDK` Nasdaq standalone listing 2025-02-24, `USD` 2x leveraged ETF). Committed evidence copy to `reports/data_manifests/massive_stocks_1m_51e9b529de55.json`.
4. **Credential Security:** Enforced strict credential handling via `MASSIVE_API_KEY` environment variable and gitignored local `.env`. The key is never logged, printed, or committed to Git.
5. **Rate-Limit Pacing:** Implemented automatic 12.5s pacing and exponential backoff on HTTP 429 (`Retry-After`) to handle Massive Basic tier constraints reliably without quota starvation.

**Reason:** Fulfills all requirements from `docs/execution_plan/MASSIVE_DATA_INGESTION.md` and `docs/execution_plan/GEMINI_MASSIVE_INGESTION_HANDOFF.md`, providing genuine verified historical market data for research gates.

## 2026-10-02 — Backtest engine event loop O(1) indexing optimization

**Decision:** Optimized `run_backtest` event loop by replacing nested $O(N)$ linear scans over bar lists and signal lists with pre-indexed $O(1)$ dictionary lookups (`bars_by_sym_ts`, `atr_by_sym`, `entry_signals_by_sym_ts`).

**Reason:** Running 16 backtests over 175,000+ 1-minute bars previously incurred over 4 billion loop iterations per backtest (~40 minutes total). Pre-indexing reduced single-backtest latency from ~150 seconds to 1.12 seconds (~130x speedup), allowing the full 3-variant comparison and bootstrap suite to complete in under 2 minutes.


