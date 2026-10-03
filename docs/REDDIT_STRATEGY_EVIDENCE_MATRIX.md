# Reddit Strategy Source-Evidence Matrix

This document provides a comprehensive component-by-component audit of the primary Reddit source:
- **Source Post:** https://www.reddit.com/r/wallstreetbets/comments/1wtmanz/made_550k_in_90_days_cant_stop_wont_stop/
- **Post Date:** 2026-09-29
- **Research Access Date:** 2026-10-02

Per `AGENTS.md` and `docs/execution_plan/REDDIT_STRATEGY_FIDELITY_EXECUTION_PLAN.md`, all behaviors are categorized using strict epistemic labels:
- `OBSERVED`: Directly stated in the Reddit post or author's comment thread.
- `DERIVED`: Necessary mechanical or structural inference from observed facts.
- `HYPOTHESIS`: A plausible deterministic proxy chosen to approximate discretionary chart reading.
- `ASSUMPTION`: A specific parameter or boundary value chosen because the source is silent.
- `UNVERIFIED`: A source claim or behavior that cannot be corroborated with available data.

---

## 1. Master Evidence Matrix

| Component | Evidence | Label | Source Location | Deterministic Implication | Data Required | Status |
|---|---|---|---|---|---|---|
| **1. Primary Equities** | Author states: "traded SNDK, MU, and SKHY". | `OBSERVED` | Primary post body | Portfolio tradable universe must include `MU`, `SNDK`, and `SKHY`. | 1-minute historical OHLCV for MU, SNDK, SKHY. | **VALIDATED** (Massive verified dataset 2026-07-01 to 2026-09-30). |
| **2. Leveraged ETF** | Author states: "held large positions in MU/SNDK/SKHY plus 2× ETFs". | `OBSERVED` | Primary post comments | Engine must support 2x semiconductor ETF exposure (e.g. `USD` ProShares Ultra Semiconductors). | 1-minute historical OHLCV for 2x semiconductor ETF (`USD`). | **VALIDATED** (Massive verified dataset 2026-07-01 to 2026-09-30). |
| **3. Benchmark Equities** | AMD mentioned as reference; SMH/SPY used as sector/market context. | `DERIVED` | Context / spec | Benchmarks (`SMH`, `SPY`, `AMD`) are used for market regime assessment, not traded as high-beta clone core. | 1-minute historical OHLCV for `SMH`, `SPY`, `AMD`. | **VALIDATED** (Massive verified dataset 2026-07-01 to 2026-09-30). |
| **4. Trading Style** | Author describes activity as "scalping and swing trading" with active management. | `OBSERVED` | Primary post body | Short-to-medium holding horizons; dynamic entry and exit rather than passive buy-and-hold. | Intraday price series. | **VALIDATED** (Intraday execution supported). |
| **5. Entry Mechanism (Discretionary)** | Author describes "watching charts, identifying trends, and deciding when to enter/exit". | `OBSERVED` | Primary post comments | The actual entries were human discretionary chart-reading decisions, not an automated mathematical algorithm. | N/A (Discretionary action cannot be read directly from tape). | **OBSERVED DISCRETIONARY** (No algorithmic formula existed). |
| **6. Entry Proxy (Trend + Pullback)** | Buying dips inside an upward-trending semiconductor market. | `HYPOTHESIS` | Strategy spec / derivation | Deterministic proxy: enter when short-term price pulls back while medium-term trend and sector momentum remain constructive. | Intraday OHLCV, moving averages, rolling volatility. | **HYPOTHESIS PROXY** (Must remain parameterized and labeled). |
| **7. Pullback Threshold Formula** | Using a specific z-score threshold (e.g. `z <= -1.5`) or ATR displacement. | `ASSUMPTION` | Engine implementation | Specific mathematical thresholds are developer assumptions, not observed Reddit rules. | Standardized feature calculations. | **ASSUMPTION** (Must NOT be called "the Reddit rule"). |
| **8. Order Types (Stop-Limits)** | Author explicitly states: "used stop limits and traded frequently because the names can move substantially". | `OBSERVED` (Order Type) / `HYPOTHESIS` (Entry Mechanics) | Primary post comments | `OBSERVED`: The trader used stop-limit orders. `HYPOTHESIS`: Directional reconstruction models entry as a stop-limit order with limit price at bar close; not an observed source entry rule. | Bar OHLC with conservative intra-bar sequencing. | **VALIDATED SIMULATION MECHANICS** (`OrderType.STOP_LIMIT` implemented and tested with gap bypass). |
| **9. Covered Calls on Strength** | Author states: "began using short-dated covered calls during strength and buying them back on pullbacks". | `OBSERVED` | Primary post comments | Short call write must be conditional on: (1) holding >= 100 shares of underlying, (2) underlying in strength/overbought state, (3) short DTE. | Historical option chain quotes with bid/ask for relevant underlying. | **UNVALIDATED** (No historical tick option-chain data currently ingested). |
| **10. Call Repurchase on Pullback** | Author explicitly buys back covered calls during pullbacks to harvest premium and release upside. | `OBSERVED` | Primary post comments | Option position must monitor underlying/option pullback and execute buy-to-close order before expiration. | Continuous intraday option pricing during pullback bars. | **UNVALIDATED** (Historical option chain quotes absent). |
| **11. Call Strike / DTE Specifics** | Precise DTE range (1-14 days), moneyness (OTM vs ATM), delta target. | `ASSUMPTION` | Strategy spec | Unspecified by author; must remain parameterized research assumptions. | Option Greeks and expiration calendar. | **ASSUMPTION** (Configurable in options module). |
| **12. Option Assignment Risk** | Delivered shares upon in-the-money expiration; cash settlement / delivery. | `DERIVED` | Mechanics of short call | When short call expires in-the-money, underlying shares are called away at strike price. | Expiration bar price vs strike. | **VALIDATED MECHANICS** (Implemented in `assignment.py`). |
| **13. Margin Usage** | Author states: "held large positions... using margin", "$1.2m figure was net liquidation value after margin debt". | `OBSERVED` | Primary post comments | Portfolio must model margin financing, margin debt tracking, borrowing interest, and buying power constraints. | Daily/intraday margin interest rate and equity tracking. | **VALIDATED MECHANICS** (Implemented in `PortfolioTracker` & `margin.py`). |
| **14. Leverage Multiplier** | Exact gross leverage (1.5x, 2.0x, 3.0x) used by the trader. | `ASSUMPTION` | Strategy spec | Author states they held large margin positions but does not disclose portfolio-level leverage formula. | Portfolio equity and gross position value. | **ASSUMPTION** (Must be evaluated via sensitivity sweep, not assumed). |
| **15. Margin Call Avoidance** | Author states: "experienced losses and avoided margin calls". | `OBSERVED` | Primary post comments | Strategy operated within broker maintenance constraints without triggering broker liquidation. | Maintenance requirement calculation (e.g. 25-50% margin). | **VALIDATED MECHANICS** (Implemented in `is_margin_call`). |
| **16. Extended-Hours Trading** | Author states: "traded SKHY/Kioxia-related exposure outside U.S. regular hours". | `OBSERVED` | Primary post comments | Activity occurred in pre-market (04:00-09:30 ET), post-market (16:00-20:00 ET), or foreign exchanges (KRX: 000660). | Extended-hours 1-minute quotes or foreign exchange feeds. | **UNVALIDATED** (Current dataset is strictly 09:30-16:00 ET RTH). |
| **17. Capital Rotation** | Rotating capital among MU, SNDK, SKHY, and 2x ETFs based on relative opportunity. | `DERIVED` | Trading notes | Author did not hold all names statically; concentrated into the highest-momentum mover. | Multi-symbol simultaneous ranking and dynamic capital allocation. | **HYPOTHESIS PROXY** (Multi-symbol sizing supported). |
| **18. Total Trade Count (~1,300+)** | Author self-reports "1,300+ trades" over approximately 90 calendar days. | `OBSERVED CLAIM` | Primary post title/body | Over 63 trading days, 1,300 trades implies ~20.6 trades/day across the portfolio (~4-5 trades/symbol/day). | Trade log summary. | **DESCRIPTIVE PLAUSIBILITY CHECK ONLY** (Must NOT be an optimization objective). |
| **19. Financial Outcome ($550k profit)** | Author self-reports ~$550k profit on ~$650k-$1.2M capital over ~90 days. | `OBSERVED CLAIM` | Primary post title | Unverified self-report from anonymous social media; subject to survivorship and reporting bias. | Brokerage clearing statements (unavailable). | **UNVERIFIED CLAIM** (Must NEVER be an optimization target). |
| **20. Cash Withdrawal ($220k)** | Author claims withdrawing $220k in cash during the run. | `OBSERVED CLAIM` | Primary post comments | Capital was removed from trading account during the period. | Clearing statements. | **UNVERIFIED CLAIM** (Not modeled in core historical P&L). |

---

## 2. Component Decoupling Architecture

Based on this evidence audit, the strategy must be strictly decomposed into four distinct layers:

```
+-----------------------------------------------------------------------------------+
| LAYER 4: SESSION / EXTENDED HOURS [STATUS: UNVALIDATED]                           |
| Non-RTH trading (SKHY / Kioxia pre-market, post-market, foreign venue)            |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
| LAYER 3: CAPITAL, LEVERAGE & MARGIN [STATUS: VALIDATED MECHANICS / ASSUMED LEV]   |
| Gross exposure bounds, margin debt, interest accrual, maintenance, liquidation   |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
| LAYER 2: COVERED-CALL OVERLAY [STATUS: UNVALIDATED - NO CHAIN DATA]               |
| Strength-based writing, DTE/moneyness, pullback repurchase, assignment mechanics  |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
| LAYER 1: DIRECTIONAL EQUITY TACTICAL TRADING [STATUS: PARTIALLY VALIDATED]        |
| Trend context, pullback entry proxy, stop-limit order model, holding horizon exits|
+-----------------------------------------------------------------------------------+
```

---

## 3. Strict Boundary Commitments

1. **No Conflation of Layers:** Directional equity trading P&L must be computed and reported independently of option premium overlays.
2. **Options Validation Barrier:** Until historical option-chain tick data (bid, ask, strike, expiration, timestamp) is ingested, options P&L will **not** be included in headline research results and will remain flagged as `UNVALIDATED`.
3. **Session Validation Barrier:** Until verified extended-hours data is ingested, non-RTH trading will remain flagged as `UNVALIDATED`.
4. **Prohibition of Retroactive Tuning:** No parameter shall be tuned to match $550k return, 1,300 trades, or positive Sharpe.
