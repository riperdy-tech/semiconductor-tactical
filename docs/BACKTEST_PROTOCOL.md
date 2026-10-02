# Backtest Protocol

## 1. Goal

Produce a backtest that can survive hostile review. A result that depends on an optimistic fill assumption is not a valid result.

## 2. Time model

All timestamps are timezone-aware.

Store raw market timestamps in the source timezone and normalize to UTC internally. Reports should also show the exchange-local timezone.

Signal calculation at time `t` may use only data timestamped <= `t`.

Default fill rule:

> signal confirmed at bar close -> fill at next eligible quote/bar.

No same-bar close execution unless a higher-resolution data source proves that execution was possible.

## 3. Intrabar ambiguity

If OHLC data shows both stop and target prices were touched in the same bar but does not reveal sequence:

- use the conservative order for the strategy under test;
- document that assumption;
- do not choose whichever sequence makes the strategy look better.

Tick/quote data may replace this assumption when available.

## 4. Costs

Equity costs must include, as configurable inputs:

- commissions;
- exchange/regulatory fees where relevant;
- bid/ask spread;
- slippage;
- market-impact proxy for large orders.

Options additionally require:

- option bid/ask spread;
- contract multiplier;
- assignment/early-exercise mechanics where relevant;
- option fees.

Margin additionally requires financing cost.

## 5. Liquidity

An order may not fill more than a configurable fraction of observed bar volume unless using quote-level data.

The engine must flag trades whose assumed size is inconsistent with available liquidity.

## 6. Corporate actions

Use split-adjusted pricing consistently, but preserve raw identifiers and corporate-action events. Never mix adjusted prices with unadjusted option strikes without conversion.

Delistings and ticker changes must not be silently removed.

## 7. Walk-forward structure

Default research split:

- training/calibration period;
- validation period;
- untouched out-of-sample test period.

Parameters are selected on training/validation only. The test period is evaluated exactly once for the formal experiment.

The exact date ranges should be specified in the run configuration, not hidden in code.

## 8. Regime robustness

At minimum compare:

- strong bull / high-momentum semiconductor regime;
- high-volatility selloff;
- sideways / low-volatility regime;
- broad-market risk-off;
- earnings-heavy windows.

## 9. Parameter robustness

For each primary parameter, perturb around the selected value and evaluate a neighborhood. A strategy whose result exists only at one exact parameter point should be labeled fragile.

## 10. Monte Carlo / resampling

At minimum implement:

- trade-order bootstrap;
- return-sequence permutation where meaningful;
- block bootstrap for autocorrelated intraday returns;
- randomized entry timing within an allowed execution window.

The output should show distribution of terminal return and drawdown, not just one equity curve.

## 11. Data leakage checks

Add automated tests for:

- future bar access;
- future option chain access;
- future corporate action information;
- future event calendars;
- universe membership leakage;
- cross-symbol timestamp misalignment.

## 12. Reproducibility

Every run must emit:

`run_manifest.json`

containing:

- run ID;
- code commit;
- config hash;
- data file hashes or provider version;
- date range;
- symbols;
- timeframe;
- strategy variant;
- random seed;
- cost model;
- leverage model;
- options model;
- output artifact paths.
