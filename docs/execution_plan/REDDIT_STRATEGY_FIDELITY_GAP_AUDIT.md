# Reddit Strategy Fidelity Gap Audit

> **AUTHORITATIVE FIDELITY AUDIT DECLARATION:**
> 
> **The current z-score/ATR strategy is a HYPOTHESIS/ASSUMPTION mechanical proxy, not an observed source rule.**
> 
> The initial backtest implementation (`CURRENT_MECHANICAL_PULLBACK_BASELINE`) constructed an automated statistical mean-reversion algorithm. While conceptually inspired by the source's mention of "pullbacks", it was an unverified engineering hypothesis rather than a faithful representation of the discretionary scalping, swing trading, stop-limit execution, and covered-call harvesting described in the primary Reddit source.

---

## 1. Systemic Fidelity Gap Analysis

This audit systematically evaluates each component of the current tactical engine against the primary source evidence documented in `docs/REDDIT_STRATEGY_EVIDENCE_MATRIX.md`.

---

### 1.1 Entry Trigger: Short-Term z-Score Displacement

1. **What does the engine currently do?**
   The engine computes a 60-bar rolling mean and rolling standard deviation of close prices:
   $$\text{zscore} = \frac{\text{close} - \mu_{60}}{\sigma_{60}}$$
   It generates an `ENTER_LONG` signal on any minute bar where $\text{zscore} \le -1.5$.
2. **What does the source actually describe?**
   The author describes discretionary chart reading: watching intraday charts, observing general upward momentum in semiconductor memory names (MU, SNDK, SKHY), and entering when names pull back during bull runs or market weakness. The author never mentions z-scores, standard deviations, or rolling mathematical formulas.
3. **Epistemic Label:** `HYPOTHESIS` (the concept of buying dips in an uptrend) / `ASSUMPTION` (the specific rolling 60-bar window and -1.5 threshold).
4. **Does the mismatch materially affect P&L?**
   **Critically.** In 1-minute high-frequency data, a -1.5 z-score trigger fires repeatedly during strong downtrends (catching falling knives) and triggers over 117,000 signal opportunities across 3 months. When coupled with tight ATR exits, it forced 5,082 roundtrips with a 2.0-minute median hold time, causing catastrophic slippage destruction ($84,998 slippage paid on a $100k account).
5. **Can the current dataset support a better implementation?**
   Yes. 1-minute OHLCV data can evaluate multi-timeframe trend alignment (e.g. 15-minute / 60-minute moving average slope) and measure structured pullbacks (e.g., price pulling back to moving average or support within an established intraday trend) rather than high-frequency noise spikes.
6. **Minimum change required:**
   Formally isolate the z-score rule as `CURRENT_MECHANICAL_PULLBACK_BASELINE`. Introduce `DIRECTIONAL_FIDELITY_RECONSTRUCTION` with explicit multi-timeframe trend confirmation and structured pullback detection, eliminating rapid-fire tick churn.

---

### 1.2 Volume Filtering: Relative Volume Filter

1. **What does the engine currently do?**
   Computes a 20-bar rolling average volume and requires current bar volume $\ge 0.70 \times$ average volume (`rel_volume >= 0.7`).
2. **What does the source actually describe?**
   The author mentions that these names "can move substantially" and liquidity is high in MU and 2x ETFs, but does not specify an explicit bar-by-bar volume threshold.
3. **Epistemic Label:** `ASSUMPTION`.
4. **Does the mismatch materially affect P&L?**
   Moderate. On low-volume instruments like `USD` (median bar volume 793 shares), this filter does not prevent illiquid intervals from filling at fixed 5 bps slippage, but on high-volume names (MU, AMD) it is largely non-restrictive.
5. **Can the current dataset support a better implementation?**
   Yes. Minimum liquidity thresholds (e.g. dollar-volume participation caps) and spread/volume checks can be explicitly evaluated.
6. **Minimum change required:**
   Retain as an explicit parameterized execution filter labeled `ASSUMPTION`.

---

### 1.3 Benchmark & Sector Trend Regime Filter

1. **What does the engine currently do?**
   `literal_clone` and `risk_controlled` disable the benchmark filter (`sector_filter: false`), trading purely on single-ticker signals. `regime_adapted` requires `SMH` 60-bar fast MA $\ge$ slow MA.
2. **What does the source actually describe?**
   The author explicitly traded during an explosive macro semiconductor bull run driven by AI memory demand (HBM / NAND / DRAM memory cycle for MU, SNDK, SKHY), actively riding sector momentum.
3. **Epistemic Label:** `OBSERVED` (trading memory names in a semiconductor supercycle) / `HYPOTHESIS` (using SMH 60-bar MA as a sector gate).
4. **Does the mismatch materially affect P&L?**
   **Decisively.** When sector filtering is active (`regime_adapted`), trades drop from 5,082 to 1,114 and net loss shrinks from -92.9% to -34.9%. Trading against the sector trend in high-beta names is lethal.
5. **Can the current dataset support a better implementation?**
   Yes. Ingested `SMH` and `SPY` 1-minute bars provide clean sector and broad-market trend state.
6. **Minimum change required:**
   Decouple sector regime from strategy variant naming. Make macro/sector trend alignment a modular filter labeled `HYPOTHESIS`.

---

### 1.4 Exits: Fixed ATR Stops and Profit Targets

1. **What does the engine currently do?**
   Exits positions upon touching entry price $\pm 1.0 \times \text{ATR}_{14}$ computed at entry bar, or upon reaching a 120-minute maximum holding time.
2. **What does the source actually describe?**
   The author describes "scalping and swing trading", using "stop limits", letting winning positions run into covered-call write zones, and actively managing positions over hours to days. The author does not describe a symmetrical 1.0x ATR bracket exit.
3. **Epistemic Label:** `ASSUMPTION` (1.0x ATR target, 1.0x ATR stop).
4. **Does the mismatch materially affect P&L?**
   **Severely.** A 1.0x ATR target on 1-minute bars is typically $0.15–$0.40 on a $100 stock. At that scale, 5.0 bps fixed slippage on entry and exit ($0.10 roundtrip) consumes 25%–50% of the entire gross profit target, guaranteeing negative mathematical expectancy under any random or near-random entry distribution.
5. **Can the current dataset support a better implementation?**
   Yes. Wider swing targets, trailing stops, or trend-exhaustion exits better match "swing trading" and allow the gross profit to comfortably exceed execution costs.
6. **Minimum change required:**
   Model swing horizons and trailing stops as alternative exit families. Retain ATR bracket under `CURRENT_MECHANICAL_PULLBACK_BASELINE`.

---

### 1.5 Holding Horizon: Maximum Hold Period and Median Hold Time

1. **What does the engine currently do?**
   Configured with `max_hold_minutes: 120`. However, because of the tight 1.0x ATR stop/target, the empirical **median holding time is only 2.0 minutes**, with positions turning over up to 79.4 times per day.
2. **What does the source actually describe?**
   The author mentions swing trading and scalping, reporting ~1,300 trades across ~90 calendar days. With 63 trading days and 4–5 symbols, 1,300 trades represents approximately **4 to 5 trades per symbol per day**, implying average holding periods of **several hours to several days**, NOT 2 minutes!
3. **Epistemic Label:** `DERIVED` (holding period inference from trade count and swing trading description).
4. **Does the mismatch materially affect P&L?**
   **Completely.** The baseline's 79 trades/day is ~16x higher turnover than the source's descriptive trade frequency (~5 trades/day/symbol). This hyper-turnover magnified transaction costs by an order of magnitude.
5. **Can the current dataset support a better implementation?**
   Yes. 1-minute data over 3 months supports holding horizons from 15 minutes to multiple days.
6. **Minimum change required:**
   Report trade duration distributions and align swing proxy parameters to test multi-hour holding horizons without tuning to the exact 1,300 number.

---

### 1.6 Session Coverage: 1-Minute RTH vs. Extended Hours

1. **What does the engine currently do?**
   Evaluates strictly regular trading hours (09:30:00 to 15:59:59 ET, Monday–Friday). Pre-market and post-market bars are omitted.
2. **What does the source actually describe?**
   Author states: "also traded SKHY/Kioxia-related exposure outside U.S. regular hours."
3. **Epistemic Label:** `OBSERVED` (trading outside U.S. RTH) / `UNVERIFIED` (foreign execution records unavailable).
4. **Does the mismatch materially affect P&L?**
   Potentially significant for SKHY. SKHY's primary listing trades on the Korea Exchange (KRX: 000660) during Asian hours; U.S. ADR trading often gaps overnight based on Asian session movement.
5. **Can the current dataset support a better implementation?**
   No. The current verified dataset (`massive_stocks_1m_51e9b529de55`) is filtered strictly to U.S. RTH. Extended-hours data was not provided.
6. **Minimum change required:**
   Explicitly declare `EXTENDED_HOURS_REPLICATION_STATUS = UNVALIDATED`. Report that non-RTH trading is excluded due to data availability constraints.

---

### 1.7 Options Overlay: Covered Calls Disabled

1. **What does the engine currently do?**
   `options.enabled: false` in `configs/historical_1m.yaml`. Option trading was completely disabled during the historical run.
2. **What does the source actually describe?**
   Author states: "began using short-dated covered calls during strength and buying them back on pullbacks." The author presents covered calls as an integral part of their trading process and P&L.
3. **Epistemic Label:** `OBSERVED` (use of covered calls) / `UNVALIDATED` (no historical option chain data).
4. **Does the mismatch materially affect P&L?**
   Unknown. Selling short-dated OTM calls during rapid rallies generates cash premium but caps upside on parabolic moves. In a strong bull market, covered calls can significantly reduce net return unless bought back skillfully.
5. **Can the current dataset support a better implementation?**
   No real historical option tick/minute quotes are present. Theoretical Black-Scholes pricing is prohibited by `AGENTS.md` Rule 7.
6. **Minimum change required:**
   Model the covered-call architecture cleanly, but strictly enforce `OPTIONS_REPLICATION_STATUS = UNVALIDATED` until verified option chain data is provided. Never mix synthetic options P&L into equity results.

---

### 1.8 Leverage, Layering, and Capital Allocation

1. **What does the engine currently do?**
   - `literal_clone`: 1.5x max gross leverage, 50% max symbol weight, max 2 layers.
   - `risk_controlled`: 1.0x max gross leverage, 25% max symbol weight, max 1 layer.
   - Sizing uses fixed dollar risk based on distance to stop.
2. **What does the source actually describe?**
   Author states they "held large positions... plus 2× ETFs, using margin", had a net liquidation value of $1.2M with substantial margin debt, experienced losses, and avoided margin calls. Exact leverage was not specified.
3. **Epistemic Label:** `OBSERVED` (margin and 2x ETF usage) / `ASSUMPTION` (specific leverage multipliers).
4. **Does the mismatch materially affect P&L?**
   Substantial. Sizing with leverage on a negative-expectancy strategy accelerates equity decay; on a positive-expectancy strategy it amplifies gains.
5. **Can the current dataset support a better implementation?**
   Yes. Gross leverage and margin debt are fully modeled with realistic interest rates and maintenance constraints.
6. **Minimum change required:**
   Retain leverage as a parameter sweep (`1.0x` to `3.0x`) labeled `ASSUMPTION`, keeping equity signal evaluation un-leveraged (1.0x) as the primary edge test.

---

### 1.9 Order Execution Model: Market vs. Stop-Limit

1. **What does the engine currently do?**
   Generates `OrderType.MARKET` orders filling at next bar's `open +/- slippage`.
2. **What does the source actually describe?**
   Author explicitly states: "used stop limits and traded frequently because the names can move substantially."
3. **Epistemic Label:** `OBSERVED` (use of stop limits).
4. **Does the mismatch materially affect P&L?**
   Yes. Stop-limits control maximum slippage on breakout or stop-loss executions, but introduce execution risk (unfilled orders when price gaps beyond limit).
5. **Can the current dataset support a better implementation?**
   Yes. 1-minute OHLC bars can accurately simulate stop-limit triggers and test limit-breach eligibility.
6. **Minimum change required:**
   Implement formal `OrderType.STOP_LIMIT` execution semantics in `ExecutionSimulator` with trigger price, limit price, and gap-bypass handling.

---

## 2. Summary of Audit Conclusions

| Dimension | Baseline Implementation | Observed Source Behavior | Fidelity Status |
|---|---|---|---|
| **Underlying Equities** | MU, SNDK, SKHY, AMD, USD | MU, SNDK, SKHY, 2x ETFs | **Alike (Verified Data)** |
| **Entry Trigger** | 1m z-score <= -1.5 (mean-reversion) | Discretionary trend + dip buying | **Mismatch (Hypothesis Proxy)** |
| **Exit Mechanism** | 1.0x ATR tight stop/target (2m hold) | Swing & scalp management (hours/days) | **Mismatch (Assumption Proxy)** |
| **Trade Frequency** | 70–80 trades/day | ~20 trades/day (~4-5/sym/day) | **16x Frequency Divergence** |
| **Covered Calls** | Disabled (false) | Active write on strength / buyback on dip | **Omitted (Data Unvalidated)** |
| **Order Execution** | Next-bar market orders | Stop-limit orders | **Partial (Needs Stop-Limit)** |
| **Session Hours** | RTH only (09:30–16:00 ET) | RTH + non-RTH SKHY/Kioxia | **Partial (Non-RTH Unvalidated)** |
| **Leverage** | Fixed 1.0x / 1.5x limits | Discretionary margin debt | **Parameter Assumption** |

The baseline proved that high-frequency z-score mean-reversion with tight ATR exits in high-beta semiconductor names fails under realistic execution costs. Phase H now reconstructs the architecture to faithfully model the source components.
