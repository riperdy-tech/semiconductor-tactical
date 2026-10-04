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

## 2026-10-02 — Post-first-real-run audit: ATR exit geometry freeze, diagnostics, and OOS boundaries

**Decision:**
1. **First-Run Evidence Preservation:** Preserved run ID `fad5c527-803f-49b7-98cc-4564b467df09` under `reports/historical_comparison_fad5c527_20261002_141140/` along with dataset manifest `reports/data_manifests/massive_stocks_1m_51e9b529de55.json` (aggregate SHA: `51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8`).
2. **Fixed ATR Exit Geometry at Entry:** Fixed an exit geometry inconsistency where stops/targets were dynamically recomputed against current bar ATR rather than entry ATR. Stored `stop_price`, `target_price`, and `entry_atr` in `PortfolioTracker` upon entry fill, ensuring trade exits are completely immutable to subsequent volatility expansion (preventing stop widening) or contraction (preventing premature exit). Added 5 regression tests in `tests/test_atr_exit_geometry.py`.
3. **Trade-Frequency & Market Exposure Diagnostics:** Added full diagnostic telemetry in `BacktestResult`, `PerformanceMetrics`, and reports: trades/day, trades/sym/day, median holding time (minutes), fills vs signals ratio, maximum simultaneous positions, re-entries, and time in market (%).
4. **Execution Cost & Financing Decomposition:** Separated gross P&L from transaction costs (commissions, slippage, margin interest financing) and reported cost drag as a percentage of gross P&L.
5. **Frozen Chronological OOS Partitions:** Frozen in `configs/historical_1m.yaml`:
   - Start: `2026-07-01T00:00:00Z`
   - Train End: `2026-08-15T00:00:00Z` (32 trading sessions)
   - Validation End: `2026-09-01T00:00:00Z` (11 trading sessions)
   - Test Start: `2026-09-01T00:00:00Z`
   - End: `2026-09-30T23:59:59Z` (21 trading sessions)
   Partitions are strictly pairwise-disjoint and chronologically ordered. Test period remains completely untouched.
6. **Explicit Documentation of Signal Semantics:** Added Section 6 and Section 8 in canonical reports documenting exact rules for `literal_clone`, `risk_controlled`, and `regime_adapted` with strict `OBSERVED`, `DERIVED`, `HYPOTHESIS`, `ASSUMPTION`, and `UNVERIFIED` tags without silent strategy substitution.
7. **No Parameter Optimization:** Confirmed that no strategy parameters (pullback z-score, volume threshold, leverage, stop/target multiples) were adjusted to improve the negative returns.

**Reason:** Fulfills all requirements from `docs/execution_plan/POST_FIRST_REAL_RUN_AUDIT.md`, `docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md`, and `docs/execution_plan/POST_FIRST_RUN_ACCEPTANCE_TESTS.md`.

## 2026-10-02 — OOS and provenance reconciliation

**Decision:**
1. **Holdout Scope Classification:** Classified the September 2026 test segment as `POST_HOC_HOLDOUT / NOT_PRISTINE_OOS`. Because the complete July–September dataset was evaluated in the initial historical run (`fad5c527`) before partition boundaries were defined, September was exposed to the research process and cannot be described as an untouched or pristine OOS dataset.
2. **Pristine OOS Availability Status:** Explicitly set `pristine_oos_status = "PRISTINE_OOS_UNAVAILABLE"` in the manifest and research report, affirming that a pristine OOS test requires an uninspected subsequent period beyond 2026-09-30.
3. **Reconciliation of Aggregate Data Hash Discrepancy:** Proved that all 7 CSV files in `data/processed/` are byte-for-byte identical to the original Massive download. The discrepancy between `51e9b529de55...` (in the Massive manifest) and `e0287562eeff...` (in the historical comparison report) arose solely from different hashing algorithms (`massive.py` hashed sorted `{sym}:{sha256}`, while `historical.py` hashed `{sym}:{sha256}:{row_count}`). Reconciled `load_historical_universe` to use the authoritative manifest aggregate hash `51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8`.
4. **Reconciliation of Run Economics:** Verified via Git commit `0d2adbc`, `run_manifest.json` (`config_hash: 0d34835d97140803`), and `comparison_metrics.json` that the post-audit run `2e9f108d` was executed strictly with `equity_commission_bps: 0.0` ($0.00 commission paid), `equity_slippage_bps: 5.0`, and `margin_rate_annual: 0.05` ($0.04 margin interest paid). Documented that the $0.005/share commission and 8% margin mentioned in the previous chat response were an assistant documentation error misquoting older `configs/base.yaml` notes, rather than the actual configuration of the run.
5. **Run Manifest Schema Extension:** Extended `RunManifest` and `create_manifest` with `dataset_id`, `aggregate_data_hash`, explicit research boundaries (`research_start`, `train_end`, `validation_end`, `test_start`, `research_end`), `oos_scope_classification`, and `pristine_oos_status`.
6. **Machine-Readable Reconciliation Artifact:** Generated and committed `reports/data_manifests/provenance_reconciliation.json` (and `reports/provenance_reconciliation.json`) documenting all dataset hashes, run IDs, Git commits, config hashes, economic settings, and scope classifications.
7. **Stop Software Changes:** Enforced stop condition upon completion of reconciliation gate without altering strategy parameters, thresholds, leverage, or costs.

**Reason:** Fulfills all requirements from `docs/execution_plan/OOS_PROVENANCE_RECONCILIATION.md` and Phase G of `docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md`.

## 2026-10-02 — USD data quality audit: zero-trade intervals and doctor-data reporting

**Decision:**
1. **Resolution of USD 4,610 Missing Slots:** Audited the 4,610 missing minute slots in `data/processed/USD.csv` (81.53% RTH coverage). Confirmed via microstructure analysis that 84% are 1-3 minute gaps (max gap = 10m; 0 gaps > 15m) concentrated during midday/afternoon lulls (0.8% missing at open, 23.3% at 14:00 ET). Verified that USD's median bar volume is only 793 shares (min = 100 shares / 1 round lot). These represent **legitimate zero-trade intervals on the consolidated tape (SIP)**, not vendor transmission drops or API interruptions.
2. **Backtest Treatment & Bias Assessment:**
   - Pending orders for USD wait until the next printed trade bar and fill at `next_bar.open +/- slippage`.
   - 0 out of 107 USD trades were entered or exited after a >1m gap; 100% triggered during active contiguous trading.
   - Sizing and execution drag: Fixed 5 bps slippage accounts for 100% of gross losses on USD ($10,051 slippage vs -$10,023 gross P&L, 2.8% win rate). Excluding USD improves portfolio net return from -92.89% to -71.89%.
3. **Diagnostic Tooling Transparency:** Enhanced `validate_symbol_bars` and `doctor-data` to explicitly display `RTH Cov%`, `Miss Min`, and `Gaps (>5d)` columns, distinguishing multi-day calendar gaps from intraday missing minute slots.
4. **Documentation:** Documented complete empirical findings in `docs/USD_DATA_AUDIT.md`.
5. **Stop Software Changes:** Re-enforced stop condition; no strategy parameters, entry thresholds, leverage, or costs were altered.

## 2026-10-03 — Phase H: Reddit strategy fidelity reconstruction and component decoupling

**Decision:**
1. **Preservation of Mechanical Baseline:** Preserved the original z-score pullback and ATR exit runs (`fad5c527` and `2e9f108d`) as `CURRENT_MECHANICAL_PULLBACK_BASELINE`. Formally documented that the z-score/ATR implementation is an automated `HYPOTHESIS` proxy, not the observed Reddit rule.
2. **Deconstruction of Strategy into Four Decoupled Layers:**
   - **Layer 1: Directional Equity:** Active swing trading in concentrated high-beta names (MU, SNDK, SKHY, USD) using trend-following pullback entries and stop-limit execution.
   - **Layer 2: Covered-Call Overlay:** Short-dated calls written exclusively during underlying strength and repurchased on pullbacks.
   - **Layer 3: Capital / Margin Layer:** Margin financing, interest accrual, maintenance requirement, and forced liquidation.
   - **Layer 4: Session / Extended Hours:** Non-RTH trading activity.
3. **Epistemic Classification & Data Sufficiency Gates:**
   - Every rule is labeled `OBSERVED`, `DERIVED`, `HYPOTHESIS`, `ASSUMPTION`, or `UNVERIFIED` in `docs/REDDIT_STRATEGY_EVIDENCE_MATRIX.md`.
   - **Covered Calls Status:** Declared `UNVALIDATED` because real historical option chain quotes are absent. Black-Scholes theoretical fills are strictly prohibited from headline results per `AGENTS.md` Rule 7.
   - **Extended Hours Status:** Declared `UNVALIDATED` because market data is strictly 09:30-16:00 ET RTH.
   - **Equity RTH:** `VALIDATED` using Massive verified 1-minute market data.
4. **Implementation of Directional Fidelity Reconstruction (`DIRECTIONAL_FIDELITY_RECONSTRUCTION`):**
   - Replaced rapid-fire z-score dip buying with a deterministic swing model requiring intraday trend alignment (`trend_slope > 0`, MA alignment, optional SMH sector confirmation) and dip stabilization (0.5%–3.0% from 20-bar high).
   - Modeled explicit stop-limit orders (`OrderType.STOP_LIMIT`) with ceiling price protection to prevent gap-through slippage.
   - Realigned exit horizons from 2.0-minute tick stops to multi-bar swing targets (2.5x ATR target, 1.5x ATR stop).
5. **Plausibility Diagnostics without Parameter Tuning:**
   - Tracked trades/day, trades/sym/day, and median hold time as descriptive reality checks against source claims (~1,300 trades, multi-hour/multi-day hold).
   - Strictly prohibited parameter tuning against the reported $550k profit, 1,300 trade count, or sample profitability.
6. **Fidelity Matrix CLI Runner:**
   - Implemented `run_fidelity_matrix` and `fidelity-historical` CLI in `run.ps1` producing canonical Markdown and JSON artifacts with full data provenance.

**Reason:** Fulfills all requirements from `docs/execution_plan/REDDIT_STRATEGY_FIDELITY_EXECUTION_PLAN.md` and Phase H of `docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md`.

## 2026-10-03 — Phase I: Phase H post-run research integrity correction

**Decision:**
1. **Preserved Baseline Identity Rule:** Enforced strict identity separation:
   - `CURRENT_MECHANICAL_PULLBACK_BASELINE`: Exclusively refers to the authoritative preserved historical baseline (Run `2e9f108d`, variant `risk_controlled`, leverage 1.0x, 1 layer, sector filter disabled, producing **-92.89% return across 5,082 trades**, config hash `0d34835d97140803`).
   - `MECHANICAL_PULLBACK_SECTOR_FILTERED_DIAGNOSTIC`: Any subsequent evaluation enabling the sector filter on the mechanical pullback (~ -34.88% / -35.69% return, ~1,114 / 1,129 trades) is strictly designated as a mechanical diagnostic. It is separated from the baseline.
   - `DIRECTIONAL_FIDELITY_RECONSTRUCTION`: Frozen Phase H directional swing trading hypothesis (**-53.27% return across 1,334 trades**).
2. **Parameter Provenance Ledger & POST_HOC_SPECIFIED Classification:**
   - Authored `docs/execution_plan/REDDIT_FIDELITY_PARAMETER_PROVENANCE.md` recording git commit history, dates, values, and evidence labels for all directional parameters (`pullback_min_pct`, `pullback_max_pct`, `stabilization_threshold`, `swing_target_atr`, `swing_stop_atr`, `order_execution_style`).
   - Formally classified all directional parameters as `POST_HOC_SPECIFIED` because the July 1 – September 30, 2026 dataset had already been observed in baseline runs on 2026-10-02 prior to parameter introduction in commit `3a5228b`.
   - Explicitly downgraded research validity: trade count proximity (~1,334 vs ~1,300) is a descriptive check only and cannot be treated as independent confirmation of fidelity.
3. **P&L Accounting and Reconciliation Invariant:**
   - Formalized mathematical reconciliation: `Signal-Price P&L (Pre-Slippage) - Execution Slippage - Commission Paid - Margin Interest Paid = Portfolio Net P&L = Final Equity - Initial Cash`.
   - Confirmed no double-counting of slippage: execution slippage is embedded into simulation fill prices, never deducted twice from net realized P&L.
   - Added `pre_slippage_pnl`, `net_realized_pnl`, and `portfolio_net_pnl` to `TradeRecord` and `PerformanceMetrics`.
4. **Epistemic Precision & Wording Corrections:**
   - Stop Limits: Updated to distinguish `[OBSERVED]` order type use by source from `[HYPOTHESIS]` directional entry order modeling.
   - Holding Horizon: Replaced claims of "natural swing frequency" with "reduced high-frequency churn relative to the baseline (median hold time 8.0 min vs 2.0 min)".
   - Fidelity Status: Replaced "Fidelity Gap Resolved" with "Fidelity Gap Partially Addressed — Deterministic Hypothesis Implemented".
   - Overall Research Status: Re-asserted `FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED` and `PRISTINE_OOS = UNAVAILABLE`.
5. **Artifact Preservation & Stop Condition:**
   - All historical run artifacts (`fad5c527`, `2e9f108d`, `5cf918f0`) preserved intact.
   - Re-enforced mandatory STOP CONDITION: no strategy parameter changes, no optimization reruns.

**Reason:** Fulfills all requirements from `docs/execution_plan/GEMINI_PHASE_H_POST_RUN_CORRECTION.md` and Phase I of `docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md`.

## 2026-10-03 — Phase J: Reddit Behavioral Replication V2 (US-market scope)

**Decision:**
1. **U.S.-Market Only Scope & Asian Venue Exclusion:**
   - Confined V2 execution strictly to U.S.-listed instruments. Direct execution on Korea Exchange (`000660.KS`) and Tokyo Stock Exchange (`285A.T`) is explicitly quarantined: `DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2`. Direct Asian execution is reserved for a future multi-currency research engine (V3).
2. **Instrument Universe Hierarchy & Manifest:**
   - Core Equities: `MU`, `SNDK`, and `SKHY` (U.S. ADR) classified as `SOURCE_IDENTIFIED` and `VALIDATED`.
   - Conditional U.S. ADR: `KXIAY` classified as an active U.S. OTC ADR (1:10 ratio) serving as a proxy for Tokyo Kioxia activity. Never describe as Nasdaq-listed. Kioxia confirmed in official release on Sep 15, 2026 that U.S. exchange ADS listing details remain undecided. Gated as `UNVALIDATED` pending dedicated OTC data feed.
   - 2x Leveraged ETFs: Cataloged U.S. candidates (`SKUU`, `SKHU`, `SKHL`, `MUU`, `SNDG`, `SNDU`, `SNXX`) as `CANDIDATE_PROXY`. Prohibited from `SOURCE_IDENTIFIED` status without primary evidence.
   - Generic `USD` ETF: Strictly quarantined from headline source replication.
   - Machine-readable manifest created at `reports/data_manifests/v2_us_instrument_manifest.json` with Pydantic parser at `src/tactical_engine/data/v2_manifest.py`.
3. **Multi-Layer Portfolio Process Engine (`v2_portfolio.py`):**
   - Replaced single-signal mean-reversion with a 5-layer portfolio process:
     - Layer 1 (Persistent Core): Long-lived inventory with independent cost basis and P&L.
     - Layer 2 (Tactical Sleeve): Intraday/swing scalps with add, reload, partial reduction (50%), and re-entry. Invariant: tactical reductions NEVER liquidate persistent core holdings.
     - Layer 3 (Covered-Call Overlay): Calls written strictly against owned unencumbered shares (`contracts <= shares / 100`). State machine handles write on strength, repurchase on pullback, expiration OTM, and assignment. Hard-gated as `UNVALIDATED` without real option chains.
     - Layer 4 (Account Margin): Margin debt across all holdings, 5% annual interest, 25% maintenance, liquidation prioritizes tactical before core.
     - Layer 5 (Profit Withdrawals): Segregated capital transfers tracked without inflating strategy returns.
   - Enforced zero-tolerance mathematical reconciliation invariant across all equity and cash flows.
4. **Level-2 Data Gate:**
   - Established explicit data gate: `TRUE_LEVEL2_REPLICATION = UNVALIDATED`. Synthetic order book features from OHLCV are prohibited.
5. **Parameter Pre-Registration & Contamination Control:**
   - Pre-registered a bounded candidate parameter family in `docs/execution_plan/REDDIT_V2_PARAMETER_REGISTRY.md`.
   - Quarantined Phase H post-hoc parameters (`impulse_pct_range [0.005, 0.030]`, `stabilization_ratio 0.35`, tight ATRs).
   - Classified July–September 2026 as `POST_HOC_HOLDOUT`. Status remains `PRISTINE_OOS = UNAVAILABLE`.
6. **V2 Experiment Matrix (V2-A through V2-F):**
   - Formalized 6-tier ablation protocol in `docs/execution_plan/REDDIT_V2_RESULTS_PROTOCOL.md`.
7. **Mandatory Software Stop Condition:**
   - Enforced software freeze upon passing tests and documentation. Prohibited parameter tuning to $550k, 1,300 trades, or profitability.

**Reason:** Fulfills all requirements from `docs/execution_plan/REDDIT_BEHAVIORAL_V2_EXECUTION_PLAN.md` and Phase J of `docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md`.

## 2026-10-04 — Phase K: Reddit Behavioral V2 End-to-End Implementation & Research Gate

**Decision:**
1. **Correction of Epistemic Evidence Labels:**
   - Corrected remaining V2 registry items: 2.0x gross leverage reclassified to `ASSUMPTION / HYPOTHESIS` (source mentions margin/2x products, not a strict 2.0x portfolio cap).
   - 50% tactical scale-out reclassified to `HYPOTHESIS` (source mentions active scaling/scalping, not a universal 50% rule).
   - 3/5/7 DTE reclassified to `ASSUMPTION / HYPOTHESIS` (source notes short-dated options, not exact DTEs).
   - Covered-call repurchase triggers reclassified to `HYPOTHESIS / ASSUMPTION`.
   - 60% core allocation explicitly classified as `ASSUMPTION` (research scenario assumption, not a recovered account fact).
   - Removed monthly core rebalance from default V2 behavior (`STATIC_HOLD`). Core inventory remains static unless altered by tactical interaction, option assignment, or forced margin liquidation.
2. **Default Universe Isolation & Clean Scope:**
   - Default headline universe strictly confined to `MU`, `SNDK`, and `SKHY`.
   - Generic sector ETF `USD`, candidate 2× leveraged ETFs (`SKUU`, `SKHU`, `SKHL`, `MUU`, etc.), and conditional OTC ADR `KXIAY` are strictly excluded from headline replication.
   - Asian direct venues (`000660.KS`, `285A.T`) are explicitly `OUT_OF_SCOPE_FOR_V2`.
3. **Implementation of Directional Signal Engine (`v2_signals.py`):**
   - Implemented 6-stage deterministic sequence: regime filter (60-bar SMA), directional impulse (30m $\ge 2.0\%$), pullback (50%), stabilization (5 bars above low), tactical add/reload, and tiered exits.
   - Tactical exit semantics: 50% partial exit on 50% rebound toward peak, `LOCAL_LOW` stop placed 0.2% below stabilization trough.
   - Pre-registered default parameters frozen prior to historical execution. Zero parameter search.
4. **End-to-End Backtest Engine (`v2_engine.py`):**
   - Connected 1m bars -> features -> signals -> pending orders -> `ExecutionSimulator` -> `V2PortfolioEngine`.
   - Enforced no-lookahead: bar $t$ signal -> bar $t+1$ execution.
   - Enforced core isolation: tactical exits strictly decrement tactical positions, never persistent core shares.
   - Enforced mathematical P&L reconciliation invariant across equity, slippage, commissions, and margin interest.
5. **Historical Research Runner & CLI (`run.ps1 fidelity-v2-historical`):**
   - Implemented canonical runner in `src/tactical_engine/research/v2_historical_runner.py`.
   - Runs ablation tiers V2-A (Core only), V2-B (Core + Tactical), and V2-C (Core + Tactical + Margin).
   - Data gates preserved: `TRUE_LEVEL2_REPLICATION = UNVALIDATED`, `HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED`, `DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2`, `PRISTINE_OOS = UNAVAILABLE`.
   - July 1 – September 30, 2026 classified strictly as `POST_HOC_HOLDOUT`.
   - Generates machine-readable `reports/v2_historical_comparison.json` and human-readable `reports/V2_HISTORICAL_COMPARISON.md`.
6. **Mandatory Software Stop Condition:**
   - Software changes frozen following reproducible run and test pass. No parameter tuning against July–September results.

**Reason:** Fulfills all requirements from `docs/execution_plan/REDDIT_V2_END_TO_END_IMPLEMENTATION_PLAN.md` and Phase K of `docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md`.

## 2026-10-04 — Phase L: Reddit Behavioral V2 Post-Run Audit & Accounting Correction

**Decision:**
1. **Preservation of Phase K Baseline Evidence:**
   - Preserved original Phase K run (`5080f859`, commit `1eda7cc`) and artifacts (`reports/fidelity_runs/phase_k_baseline_1eda7cc/`) intact without deletion or silent overwriting.
2. **Effective Evaluation Start Date Audit (SKHY Start Disparity):**
   - Established that SKHY 1-minute historical data starts on `2026-07-13T13:30:00Z` (22,230 bars), while MU and SNDK start on `2026-07-01` (24,960 bars).
   - Confined the common 3-asset evaluation window strictly to `2026-07-13T13:30:00Z` through `2026-09-30T19:59:00Z`.
   - Classified the pre-core interval (July 1 to July 10, 2026; 2,730 bars) as `UNINITIALIZED / NOT_IN_SAMPLE`. Eliminated pre-core tactical trading prior to SKHY and core portfolio availability.
3. **Exogenous Normalized 60% Core Allocation Semantics:**
   - Established 60% core at effective start open prices as an exogenous baseline state setup: 151 shares MU ($19,874.62), 505 shares SNDK ($19,977.80), and 1,131 shares SKHY ($19,984.77). Total starting core value is $59,223.68 (59.22% actual allocation), leaving $40,776.32 residual tactical cash.
   - Initial state setup incurs zero commissions and zero slippage.
4. **Fill Reference Price vs Execution Price & Pre-Slippage P&L Invariant:**
   - Added `reference_price` to `Fill` and simulator (`reference_price = base_price`).
   - Corrected `pre_slippage_pnl` on trade records to be calculated strictly from unadjusted fill reference prices rather than post-slippage fill prices.
   - Enforced exact mathematical invariant: `pre_slippage_pnl - slippage == realized_pnl`.
5. **Separation of Closed Tactical Realized P&L from Terminal Open Mark-to-Market P&L:**
   - Explicitly decoupled completed FIFO round-trip realized P&L from terminal mark-to-market open position P&L in reports and metrics models.
6. **Granular Trade State and Order Accounting:**
   - Separated and reported detailed counts: signals generated, order attempts, entry fills, reload fills, partial exit fills, full exit fills, completed FIFO round trips, and ending open tactical lots/shares.
7. **Lookahead Elimination in Risk Checks & Liquidation Timing:**
   - Valuation for execution-time buying power checks uses bar open prices (`execution_valuation_prices`), eliminating bar close price lookahead.
   - Margin liquidation orders triggered at bar close are scheduled for execution at next bar open rather than same-bar close.
8. **Peak Margin Debt & Financing Accounting:**
   - Sampled peak margin debt after intra-bar transactions and financing accrual.
   - Evaluated historical V2-C margin behavior: the $40,776.32 tactical cash sleeve was sufficient to fund all 108 tactical positions historically without margin borrowing ($0 peak debt, $0 financing interest). Classified as `CAPABILITY PRESENT / NOT EXERCISED HISTORICALLY`.
   - Added synthetic integration test `test_v2_c_margin_activation_synthetic` to verify leverage capacity, daily interest accrual, maintenance margin constraints, and tactical-first liquidation logic.
9. **Layered Accounting Invariant Reconciliation:**
   - Reconciled performance across reference layer, execution layer, financing layer, and terminal open mark-to-market layer, proving zero-discrepancy reconciliation to ending account equity.
10. **Zero Parameter Tuning & Scope Integrity:**
    - Directional parameters remained 100% frozen; zero parameter sweeps or optimizations performed.
    - Global epistemic statuses preserved: `FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED`, `DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2`, `TRUE_LEVEL2_REPLICATION = UNVALIDATED`, `HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED`, `PRISTINE_OOS = UNAVAILABLE`.

**Reason:** Fulfills all requirements from `docs/execution_plan/REDDIT_V2_POST_RUN_AUDIT_AND_ACCOUNTING_PLAN.md` and Phase L of `docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md`.









