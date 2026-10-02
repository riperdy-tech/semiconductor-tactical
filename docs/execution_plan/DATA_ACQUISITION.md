# Data Acquisition Plan

## Purpose

This document defines what data the repository needs before the final historical research run.

Do not fabricate missing data. Do not mark a dataset `REAL_HISTORICAL_VERIFIED` merely because a CSV looks plausible.

## Required equity universe

### Tradable symbols

- MU
- SNDK
- SKHY
- AMD
- USD

### Benchmark inputs

- SMH
- SPY

The historical comparison engine expects the benchmark inputs because `regime_adapted` uses the semiconductor and broad-market regime layer.

## Required bar resolution

### Primary research

**1-minute bars** are the priority because the strategy uses:

- pullback/z-score features;
- relative volume;
- 5m/15m/60m derived features;
- 120-minute maximum holding period;
- next-bar execution.

Daily data is useful only for sanity checks and longer-context analysis.

## Required data fields

Minimum CSV contract:

```text
timestamp,open,high,low,close,volume
```

Recommended additional fields:

```text
vwap,source,timezone,adjustment_status
```

The actual repository data contract remains authoritative.

## Corporate-action requirements

For each symbol, document:

- split adjustment policy;
- dividend treatment;
- ticker changes;
- spinoff/history caveats;
- delisting handling;
- whether prices are adjusted or unadjusted;
- how volume is treated.

### Important symbol-history issue

`SNDK` needs special treatment because the security's historical identity/ticker continuity must be documented rather than assumed. Confirm how the chosen data vendor represents its pre/post-corporate-action history before marking the dataset verified.

`SKHY` also requires source/vendor verification of the exact instrument identity and ticker history before ingestion.

`USD` must be verified as the intended 2x semiconductor ETF instrument for the strategy; do not substitute another leveraged ETF merely because it is more convenient.

## Suggested acquisition order

1. Obtain equity minute bars for all 7 required symbols.
2. Verify timestamp timezone/session semantics.
3. Verify corporate-action treatment.
4. Build one dataset manifest describing the complete source set.
5. Run the repository's data doctor/cadence validator.
6. Only then create `REAL_HISTORICAL_VERIFIED`.
7. Run the final OOS comparison.
8. Acquire option data separately; do not block equity-only research on options unless the research question explicitly depends on them.

## Data manifest requirements

The repository expects a manifest with explicit provenance. At minimum:

```json
{
  "dataset_id": "<immutable-id>",
  "data_status": "REAL_HISTORICAL_VERIFIED",
  "provider": "<vendor/source>",
  "is_verified_market_data": true,
  "source_description": "<exact source and product>",
  "license_or_citation": "<vendor/source reference>",
  "bar_resolution": "1m"
}
```

The manifest should also identify:

- coverage dates;
- symbols;
- timezone;
- adjustment policy;
- data download/export date;
- vendor dataset/product name.

## Verification checklist

Before research:

- every required symbol exists;
- all files load successfully;
- all timestamps parse correctly;
- cadence matches 1m;
- regular-session semantics are documented;
- no duplicate timestamps;
- OHLC relationships are valid;
- no impossible zero/negative prices;
- volume semantics are documented;
- corporate actions are documented;
- hashes are recorded;
- source is documented;
- all seven symbols use a compatible methodology;
- SMH/SPY align with the tradable universe's timestamp/session basis.

## Options data

Covered-call validation requires actual historical option quotes.

Minimum practical contract fields:

```text
timestamp
underlying
option_symbol
expiration
strike
bid
ask
underlying_price
volume
open_interest
```

Prefer quote-level data with bid/ask timestamps rather than end-of-day theoretical values.

Do not use Black-Scholes output as historical executable quotes.

## What counts as acceptable

A vendor/source is acceptable when it provides:

- genuine historical market observations;
- sufficient 1-minute resolution for the required period;
- documented corporate-action handling;
- a reproducible export/API;
- a source/product identity that can be cited in the manifest;
- enough historical depth for the selected Reddit-period and OOS windows.

## What does NOT count

- the synthetic fixtures in `data/sample_historical`;
- generated/random CSVs;
- data copied from an unknown website with no provenance;
- a vendor's current quote feed used as a historical substitute;
- theoretical option pricing presented as historical execution;
- silently mixing adjusted and unadjusted histories.

## Research-period rule

Do not choose the OOS dates to improve performance.

First reconstruct the relevant Reddit observation period from the source documentation, then define:

- train period;
- validation period;
- untouched final test/OOS period.

Record these boundaries in `docs/DECISIONS.md`.

## Final handoff

Once verified equity data is available:

1. place it in the configured historical data directory;
2. add the dataset manifest;
3. run the data doctor;
4. run `comparison-historical`;
5. preserve the generated manifest, hashes, and report;
6. only then interpret the results.
