# Strategy Specification

## 1. Objective

Build a deterministic research engine that approximates the observable behavior in the source post while keeping every unsupported detail parameterized.

The strategy is architecturally decoupled into four distinct layers:

1. **Layer 1: Directional Equity Layer** — short-to-medium horizon active directional trades in concentrated high-beta semiconductor names (MU, SNDK, SKHY, USD).
2. **Layer 2: Covered-Call Overlay Layer** — short-dated covered calls entered during underlying strength and repurchased on pullbacks (`UNVALIDATED` until authentic historical chain data is provided).
3. **Layer 3: Capital / Margin Layer** — position sizing, margin financing, borrowing interest, gross exposure constraints, and forced liquidation.
4. **Layer 4: Session / Extended-Hours Layer** — non-RTH trading activity (`UNVALIDATED` until verified non-RTH quotes are provided).

## 2. Strategy variants

### Baseline: `CURRENT_MECHANICAL_PULLBACK_BASELINE` (Preserved)
- **Status:** `PRESERVED_HISTORICAL_BASELINE`
- **Epistemic Classification:** `HYPOTHESIS` (mean-reversion dip buying) / `ASSUMPTION` (60-bar window, z-score <= -1.5, 1.0x ATR target/stop).
- **Description:** The original mechanical z-score pullback implementation. Preserved as an immutable empirical control proving that high-frequency noise trading with tight ATR stops yields catastrophic transaction-cost decay.

### Variant 1: `DIRECTIONAL_FIDELITY_RECONSTRUCTION`
- **Status:** `ACTIVE_RESEARCH_VARIANT`
- **Epistemic Classification:**
  - Active scalping/swing trading in high-beta names: `OBSERVED`
  - Stop-limit order execution: `OBSERVED`
  - Long-only trend-following pullback entry: `HYPOTHESIS`
  - Swing profit target (2.5x ATR) and stop (1.5x ATR): `ASSUMPTION`
- **Description:** Reconstructs the observed discretionary trading process as a deterministic swing model: requires intraday trend alignment (`trend_slope > 0`, MA alignment, optional sector trend), enters on controlled dip stabilization (0.5%–3.0% from recent high), executes via stop-limit orders with ceiling price caps, and exits on swing horizons.

### Variant 2: `DIRECTIONAL_FIDELITY_MARGIN`
- **Status:** `ACTIVE_RESEARCH_VARIANT`
- **Epistemic Classification:**
  - Margin debt and large position usage: `OBSERVED`
  - Specific leverage cap (1.5x, 2.0x, 3.0x): `ASSUMPTION`
  - 5% annual borrowing rate and 25% maintenance: `ASSUMPTION`
- **Description:** Combines `DIRECTIONAL_FIDELITY_RECONSTRUCTION` with explicit margin financing, 2 layers of entry, and liquidation monitoring to assess whether leverage can amplify genuine edge without margin call breach.

### Variant 3: `COVERED_CALL_OVERLAY`
- **Status:** `UNVALIDATED`
- **Epistemic Classification:**
  - Short-dated covered calls written on strength and bought back on dips: `OBSERVED`
  - Moneyness (OTM), DTE (1-14d), strike selection: `ASSUMPTION`
  - Option P&L attribution without chain data: `PROHIBITED`
- **Description:** Models short call writing conditional on holding >= 100 shares and underlying at strength (`check_strength_predicate`), with repurchase triggers on pullbacks. Quarantined as `UNVALIDATED` until real option chain tick data is ingested.

### Legacy Baseline Variants (Subsumed under Baseline)
- `literal_clone`: 1.5x leverage, 2 layers, no sector filter.
- `risk_controlled`: 1.0x leverage, 1 layer, fixed-risk sizing.
- `regime_adapted`: `risk_controlled` with sector trend filter.

## 3. Universe

Initial research universe:

- MU
- SNDK
- SKHY
- configurable AMD benchmark/control
- configurable 2× semiconductor ETFs

Do not hard-code the exact 2× ETF tickers until they are verified from a data provider. Treat them as configuration.

The universe should support future expansion to other high-beta names without changing the engine.

## 4. Features

At minimum calculate:

- 1m, 5m, 15m, 1h, and 1d returns;
- rolling volatility / ATR;
- distance from VWAP;
- rolling z-score of return and price displacement;
- trend slope / regime;
- relative volume;
- sector-relative return;
- cross-sectional relative strength within the universe;
- gap size;
- time-of-day;
- distance from recent high/low;
- earnings/news blackout flag where an event calendar is available.

Do not claim that these features are what the Reddit trader used. They are **mechanical proxies for discretionary chart reading**.

## 5. Equity entry hypothesis

The base hypothesis is:

> Buy a statistically significant short-term pullback when the medium-short-term trend remains intact and liquidity/sector conditions are supportive.

A proposed signal should be expressible as deterministic predicates, for example:

```text
trend_ok
AND pullback_extreme
AND sector_not_breaking_down
AND liquidity_ok
AND event_filter_ok
```

Do not finalize thresholds before the parameter sweep. Keep thresholds in YAML configuration.

## 6. Equity exits

Test at least these exit families independently:

- fixed percentage target;
- ATR-based target;
- VWAP reversion;
- prior local high / swing level;
- time-based exit;
- trailing stop;
- hard stop.

The headline report must show which exit family was used; never silently mix them.

## 7. Layered entries

Literal clone experiment may permit 2–3 layers.

Each layer must have:

- independent fill price;
- predefined maximum allocation;
- predefined maximum number of layers;
- aggregate stop / liquidation rule;
- total risk accounting.

No unbounded averaging down.

Risk-controlled variant uses fixed aggregate risk and may reject a new layer if aggregate stop-loss risk exceeds the budget.

## 8. Covered-call hypothesis

A covered call is only valid when the simulator owns at least the required underlying shares.

Entry hypothesis:

- underlying is in a strength regime;
- option has sufficient liquidity;
- option DTE is within configured short-dated range;
- strike is outside/near the chosen moneyness threshold;
- expected premium compensates for assignment/upside risk under the experiment's objective.

Repurchase hypothesis:

- underlying experiences a pullback;
- option premium falls sufficiently;
- remaining extrinsic value no longer justifies the short call;
- or underlying approaches a predefined risk/assignment threshold.

These are hypotheses. The system must support alternative rules without changing the engine.

## 9. Covered-call accounting

For every options trade record:

- underlying symbol;
- option contract ID;
- call/put;
- strike;
- expiry;
- DTE at entry/exit;
- quantity;
- bid/ask at signal and fill;
- fill price;
- premium received/paid;
- assignment state;
- realized/unrealized P&L;
- associated underlying shares;
- option transaction costs.

If historical chain data cannot support these fields, the run is not options-valid.

## 10. Capital rotation

The engine must support multiple simultaneous symbols and choose allocations by configured policies:

- equal risk;
- volatility scaled;
- signal ranked;
- top-N signal concentration;
- fixed per-symbol cap.

Capital turnover must be reported separately from return.

## 11. Leverage and margin

Leverage is a research variable, not a recommendation.

Run at minimum:

- 1.0×
- 1.25×
- 1.5×
- 2.0×
- 3.0×

subject to broker/product constraints represented by the simulator.

Margin simulation must include:

- financing rate;
- maintenance requirement;
- available buying power;
- liquidation threshold;
- forced liquidation order;
- liquidation slippage;
- overnight vs intraday rules where applicable.

## 12. Required falsification tests

The research report must answer:

1. Does the equity-only strategy remain profitable after realistic costs?
2. Does the edge survive when the 2026 semiconductor period is removed?
3. Does performance collapse if the strongest-performing ticker is removed?
4. Does the edge survive randomized entry timing within the same bar/day?
5. Does adding covered calls improve risk-adjusted return or simply cap upside?
6. Does leverage amplify a genuine edge or merely amplify one favorable regime?
7. Does a simple sector/regime filter improve out-of-sample performance?
8. Does the strategy remain positive after parameter perturbation?
9. Is performance concentrated in a tiny number of days?
10. How often does the strategy experience margin-call conditions?

## 13. Primary metrics

Report:

- total return;
- annualized return where appropriate;
- max drawdown;
- average drawdown;
- worst day/week/month;
- profit factor;
- expectancy per trade;
- win rate;
- median and tail trade P&L;
- turnover;
- costs as % of gross P&L;
- slippage as % of gross P&L;
- option premium contribution;
- directional P&L contribution;
- margin interest;
- peak gross exposure;
- peak net exposure;
- margin utilization;
- forced-liquidation count;
- time in market;
- P&L concentration by ticker and by date.

For parameter sweeps, include stability metrics rather than reporting only the best run.
