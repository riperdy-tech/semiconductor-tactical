# Experiment Matrix

The first full experiment should vary one concept at a time before attempting joint optimization.

## Signal family

- pullback z-score: [-0.5, -1.0, -1.5, -2.0]
- VWAP distance thresholds
- trend filter windows
- relative-volume filters
- sector-relative strength filters

## Exit family

- fixed % target: [0.5%, 1.0%, 1.5%, 2.0%]
- ATR target: [0.5, 1.0, 1.5, 2.0]
- time stop: [5m, 15m, 30m, 2h, 1d, 3d]

These are **research hypotheses**, not claims about the Reddit trader's exact rules.

## Position sizing

Compare:

- fixed dollar;
- fixed portfolio percentage;
- volatility scaled;
- fixed loss-at-stop.

## Layering

- none;
- 2 layers;
- 3 layers.

## Leverage

- 1.0×;
- 1.25×;
- 1.5×;
- 2.0×;
- 3.0×.

## Covered calls

Test separately:

- no options;
- short-dated OTM calls;
- short-dated near-ATM calls;
- strength trigger + pullback repurchase;
- strength trigger + time-based repurchase.

The exact DTE/delta ranges must be configurable and supported by actual historical chain data.

## Required controls

Every experiment should have these controls:

1. buy-and-hold underlying;
2. simple trend-following baseline;
3. random-entry control with matched holding time;
4. transaction-cost sensitivity;
5. best-ticker-removed test.
