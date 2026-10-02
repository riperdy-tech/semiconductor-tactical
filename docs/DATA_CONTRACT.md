# Data Contract

## Required market data

### Equity OHLCV

Preferred:

- 1-minute bars for U.S. regular session;
- premarket/after-hours if the experiment explicitly includes them;
- at least daily bars for long-horizon robustness checks.

Fields:

- timestamp;
- symbol;
- open;
- high;
- low;
- close;
- volume;
- vwap where supplied or derivable.

### Quotes

Preferred for execution validation:

- bid;
- ask;
- bid size;
- ask size;
- timestamp.

### Options

Required for validated covered-call backtests:

- timestamp;
- underlying;
- contract identifier;
- strike;
- expiry;
- call/put;
- bid;
- ask;
- mid;
- last;
- volume;
- open interest where available;
- underlying price at the same timestamp.

### Corporate actions

- splits;
- symbol changes;
- mergers/delistings where relevant.

### Market calendar

- exchange session open/close;
- holidays;
- early close;
- timezone.

### Event calendar

Optional but strongly preferred:

- earnings timestamp;
- major corporate events.

Events are a filter/input only; do not use post-event information before the event occurs.

## Data-source abstraction

Implement provider-neutral interfaces. Do not hard-code one vendor into the strategy logic.

Suggested adapters:

```text
EquityDataProvider
QuoteDataProvider
OptionChainProvider
CorporateActionProvider
CalendarProvider
EventProvider
```

## Data validation gates

Before a backtest starts, validate:

- monotonic timestamps;
- duplicate rows;
- missing bars;
- impossible OHLC relationships;
- zero/negative prices;
- suspicious volume gaps;
- split discontinuities;
- option chain consistency;
- timezone consistency.

A failed validation should stop the run or explicitly downgrade it to `research_invalid`.
