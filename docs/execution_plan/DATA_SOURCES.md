# Recommended Data Sources — 2026-10-02

## Recommended path for this repository

### Equity / ETF minute data: Massive Stocks API

**Use first.**

Massive currently offers U.S. stock/ETF historical aggregate bars down to minute resolution. The Stocks Basic tier is free, includes 2 years of historical data, all U.S. stock tickers, corporate actions, and minute aggregates; it is limited to 5 API calls/minute. Stocks Starter is $29/month and extends history to 5 years with unlimited API calls and flat files. [Verify current commercial/licensing terms before redistribution.]

This is sufficient for the current Reddit-period research because the target observation is recent and the repository needs only seven U.S.-listed instruments:

- MU
- SNDK
- SKHY
- AMD
- USD
- SMH
- SPY

Primary documentation:
- https://massive.com/pricing?product=stocks
- https://massive.com/docs/rest/stocks/aggregates/custom-bars

### Important symbol-history facts

**SKHY:** SK hynix's Nasdaq ADR began trading on July 10, 2026. Therefore U.S.-session SKHY data does not exist before that date. Do not fabricate or backfill the U.S. ADR using KRX prices inside a U.S.-market intraday backtest. SK hynix confirms the Nasdaq ADR ticker is SKHY and the ADR ratio is 1:10.

**SNDK:** Sandisk began trading independently on Nasdaq under SNDK on February 24, 2025 after its spin-off from Western Digital. Do not silently treat pre-February-24-2025 WDC/SNDK history as if it were directly traded SNDK.

**USD:** ProShares Ultra Semiconductors (USD) is the intended 2x semiconductor ETF. ProShares states that USD targets 2x the daily performance of the Dow Jones U.S. Semiconductors Index and began on January 30, 2007.

## Why Massive is the easiest first source

The research currently needs 1-minute OHLCV rather than full tick/order-book data.

Massive's stock custom-bar endpoint supports a custom date range and interval and returns OHLCV aggregates. The API supports split-adjusted or unadjusted results. Use the repository's chosen corporate-action policy consistently and record it in the dataset manifest.

For this project, prefer:

- 1-minute;
- regular session first;
- split-adjustment policy explicitly documented;
- raw/source CSV preserved before any local transformation.

Do not silently mix different vendors for different symbols unless a missing instrument forces it and the compatibility decision is documented.

## Higher-fidelity alternative: Databento

Databento is the stronger choice when we need exchange-level provenance, quotes/trades, or finer microstructure analysis.

Its U.S. equity offerings provide 1-minute OHLCV and lower-level trade/quote data, with usage-based historical pricing and $125 in initial free historical-data credits.

For options, Databento's OPRA.PILLAR dataset is particularly useful. It covers U.S. equity options from April 1, 2013 and provides schemas including:

- CBBO-1m;
- CBBO-1s;
- Trades;
- OHLCV-1m;
- definitions;
- statistics.

Primary documentation:
- https://databento.com/stocks
- https://databento.com/datasets/OPRA.PILLAR
- https://databento.com/pricing/

Use Databento when the research requires point-in-time quote detail or when Massive's history/licensing/symbology is insufficient.

## Options: recommended choices

### Option A — Databento OPRA

Best when we want rigorous point-in-time option-market data.

OPRA.PILLAR covers U.S. equity options and includes consolidated quote schemas. Historical availability begins April 1, 2013.

For the covered-call replication, prefer a quote schema containing time-stamped bid/ask information rather than relying on theoretical prices.

### Option B — Cboe DataShop

Cboe DataShop sells Option Quote Intervals with 1-minute or custom N-minute summaries. The dataset includes NBBO bid/ask, quote size, OHLC, volume, underlying bid/ask, and optional open interest. It covers U.S. listed options disseminated through OPRA.

This is attractive when a clean 1-minute option-quote dataset is preferred over raw OPRA processing.

Primary documentation:
- https://datashop.cboe.com/option-quote-intervals

### Option C — Massive Options

Massive provides historical option contracts, minute aggregates, and historical quotes with bid/ask/timestamp information. The current Options pricing page shows 2 years of historical data on Basic/Starter and deeper history on higher tiers.

This can be convenient because the equity and option data can come from the same API family, but confirm the exact plan access for historical quote endpoints before purchasing.

Primary documentation:
- https://massive.com/options
- https://massive.com/docs/rest/options/overview

## Not the first choice

### Alpha Vantage

Alpha Vantage provides premium 1-minute historical intraday OHLCV, including month-by-month historical retrieval and split/dividend-adjusted or raw values.

It is useful for spot-checking or a lightweight secondary source, but it is not the preferred primary source for this project because we want reproducible multi-symbol research, explicit provenance, and eventually historical quotes/options.

Primary documentation:
- https://www.alphavantage.co/documentation/

## Recommended acquisition sequence

### Phase A — Get the equity engine running

1. Create a Massive account.
2. Get an API key.
3. Pull 1-minute OHLCV for:
   - MU
   - SNDK
   - SKHY
   - AMD
   - USD
   - SMH
   - SPY
4. Restrict the initial dataset to the actual Reddit observation period plus enough pre-period history for warm-up features.
5. Preserve the raw exports.
6. Convert to the repository CSV contract.
7. Add `dataset_manifest.json`.
8. Run:
   `.un.ps1 doctor-data -Config configs/historical_1m.yaml -DataDir data/processed`
9. Only mark the dataset `REAL_HISTORICAL_VERIFIED` after source, symbol identity, resolution, timezone, adjustment policy, and hashes are checked.

### Phase B — Run equity-only research

Use:

```powershell
.\run.ps1 comparison-historical -Config configs/historical_1m.yaml -DataDir data/processed
```

The equity-only result can be evaluated before option data exists.

Options must remain explicitly `UNVALIDATED`.

### Phase C — Add historical options

Choose Databento OPRA, Cboe DataShop, or a sufficiently detailed Massive options plan.

Capture:

- option contract identity;
- underlying;
- strike;
- expiration;
- call/put;
- timestamp;
- bid;
- ask;
- bid size;
- ask size;
- volume;
- open interest where available;
- underlying price;
- source/vendor;
- adjustment/corporate-action context where relevant.

Then run the covered-call engine separately before incorporating option results into the headline strategy comparison.

## One important research-period caveat

The Reddit post "Made $550k in 90 days. Can't stop / won't stop" was posted September 29, 2026. A literal 90-day lookback begins around the start of July 2026.

SKHY only began Nasdaq trading on July 10, 2026.

Therefore, if the experiment is defined as the author's exact recent 90-day U.S.-market trading window, the repository should not invent SKHY U.S. trading history for the first part of that window.

Record this explicitly in `docs/DECISIONS.md` when fixing the final research dates.

## Bottom line

For the first real dataset:

**Massive Stocks Basic is the simplest place to start.**

It is free, covers the required U.S. stocks/ETFs, provides historical minute aggregates, and has 2 years of history. The current research window is comfortably inside that period.

For options:

**Databento OPRA or Cboe DataShop** is the more rigorous next step when we reach covered-call validation.
