# Massive Historical Data Ingestion Plan

## Purpose

This is the implementation contract for acquiring genuine 1-minute U.S. equity/ETF historical data from Massive and converting it into the repository's existing historical-data contract.

The objective is **data ingestion and verification only**.

Do not alter strategy parameters, signal logic, execution semantics, OOS boundaries, or experiment methodology to improve observed performance.

## Source

Massive's Stocks REST API provides custom historical OHLCV aggregates at:

`GET /v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}`

For this project the required request is:

- multiplier: `1`
- timespan: `minute`
- adjusted: `true`
- sort: `asc`
- limit: up to the API maximum supported by the account
- authentication: API key supplied through the environment, never committed to Git

Massive documents that aggregate timestamps are in Eastern Time (ET), that results can include pre-market, regular-market, and after-hours data, and that `adjusted=true` means split-adjusted data. The importer must therefore explicitly convert timestamps to UTC and explicitly select the regular U.S. session rather than assuming the endpoint returns only regular-session bars.

Reference:
https://www.massive.com/docs/rest/stocks/aggregates/custom-bars

Authentication reference:
https://www.massive.com/docs/rest

## API credential policy

Use:

`MASSIVE_API_KEY`

The key must be provided at runtime, for example on Windows PowerShell:

`$env:MASSIVE_API_KEY = "<key>"`

Never:

- put the key in Git;
- put the key in YAML;
- put the key in `.env` committed to Git;
- print the key;
- write the key to a report;
- include the key in exception messages;
- include the key in GitHub Actions logs.

The repository already ignores `.env`, so local development may use it, but the importer should prefer the environment variable.

## Required instrument universe

### Tradable instruments

- MU
- SNDK
- SKHY
- AMD
- USD

### Regime / benchmark inputs

- SMH
- SPY

The historical comparison runner already loads SMH and SPY automatically. The ingestion step must therefore download them too.

Do not substitute:

- another leveraged semiconductor ETF for USD;
- KRX SK hynix data for U.S.-listed SKHY;
- a synthetic proxy for a missing U.S.-listed series.

## Research dates

Do not hardcode the research window inside the importer.

The source notes establish that the Reddit post was dated 2026-09-29 and describes a 90-day result. The actual backtest/OOS boundaries must remain those documented by the research protocol and `docs/DECISIONS.md`.

The importer should accept explicit `--start` and `--end` arguments.

Before downloading, include enough warm-up history before the research start to support all lookback features used by the configured strategy. Do not use future data to manufacture warm-up values.

The downloader may fetch a wider window than the final OOS period, but the backtest must continue to use the configured research boundaries.

## Session policy

Massive's custom bars can include pre-market and after-hours data.

For this research dataset:

- retain U.S. regular trading hours only;
- regular session = 09:30 through 16:00 America/New_York;
- convert the retained timestamps to UTC before writing CSV;
- document the source timezone and output timezone in the dataset manifest;
- do not fill missing bars with synthetic OHLCV.

The intended minute representation is one bar beginning at each observed 1-minute bucket.

Do not silently mix extended-hours bars into the RTH strategy.

If the source uses a different timestamp convention than assumed, stop and document the actual convention before marking the dataset verified.

## Massive response -> repository CSV mapping

Massive aggregate fields:

- `t` -> timestamp
- `o` -> open
- `h` -> high
- `l` -> low
- `c` -> close
- `v` -> volume
- `vw` -> vwap when available
- `n` -> transaction_count when retained as auxiliary metadata

Repository CSV minimum:

```text
timestamp,open,high,low,close,volume
```

Recommended emitted CSV:

```text
timestamp,open,high,low,close,volume,vwap
```

Timestamp requirements:

- ISO-8601;
- explicit UTC offset or `Z`;
- monotonically increasing;
- one symbol per file.

Write:

`data/processed/<SYMBOL>.csv`

The raw API JSON should not be required by the backtester. If raw responses are retained for auditability, place them under `data/raw/massive/` and keep them out of Git.

## Adjustment policy

Use `adjusted=true` for the research dataset unless the research protocol is explicitly changed.

Document the exact policy as:

`split_adjusted`

Do not describe this as total-return or dividend-adjusted data.

Do not combine adjusted and unadjusted histories within the same dataset.

Because the engine's Bar object records an adjustment status, the importer/provenance layer should expose the manifest's policy rather than hardcoding a misleading generic label.

## Pagination and reliability

Implement pagination correctly.

The endpoint can return `next_url`. The importer must continue fetching until:

- no `next_url` remains; or
- the requested end date has been fully covered.

Do not assume a single request is sufficient.

Handle at least:

- HTTP 401/403 -> fail clearly with credential/access guidance;
- HTTP 429 -> retry with backoff and respect `Retry-After` if supplied;
- HTTP 5xx/network failure -> bounded retry with backoff;
- malformed JSON -> fail;
- missing `results` -> fail rather than silently producing an empty file.

Never convert a failed API response into a partial "verified" dataset.

## Deterministic local artifact

The importer should be idempotent.

Given:

- the same Massive source data;
- the same start/end dates;
- the same session filter;
- the same adjustment setting;
- the same importer version;

the output ordering and numerical content must be deterministic.

Sort by timestamp ascending before writing.

Use stable CSV formatting.

Avoid non-deterministic metadata in the CSV itself.

## Verification before promotion

A dataset is not `REAL_HISTORICAL_VERIFIED` merely because files downloaded successfully.

For each of the seven required symbols verify:

- file exists;
- non-empty;
- expected columns present;
- timestamp parsing succeeds;
- timestamps are timezone-aware and normalized to UTC;
- timestamps are strictly increasing;
- no duplicate timestamps;
- all OHLC values are positive;
- low <= open <= high;
- low <= close <= high;
- volume >= 0;
- data is actually 1-minute rather than daily or coarser;
- regular-session timestamps fall inside 09:30-16:00 ET after conversion;
- no unexpected pre/post-market bars remain;
- source adjustment policy is recorded;
- coverage dates are recorded;
- row count is recorded;
- SHA-256 is recorded.

### Missing-minute policy

Do **not** forward-fill or fabricate missing one-minute bars.

A missing minute can reflect a period with no qualifying trade or another market-data condition. The importer must preserve the vendor observations exactly.

Instead:

1. compute expected RTH minute slots for each trading date;
2. report observed coverage ratio;
3. report missing-slot counts;
4. report unusually large intraday timestamp gaps;
5. require manual review of material gaps before promotion to verified.

The verification report must distinguish:

- ordinary market-calendar gaps;
- zero-trade/missing aggregate intervals;
- suspicious data gaps;
- ticker-specific trading halts or data interruptions.

## Symbol-history checks

### SNDK

Document how Massive represents SNDK's historical identity around its corporate-action / standalone-listing history.

Do not infer ticker continuity solely from a file name.

Record any continuity caveat in the manifest and `docs/DECISIONS.md`.

### SKHY

Verify that the downloaded instrument is the U.S.-listed Nasdaq ADR ticker SKHY.

Do not splice Korean-market SK hynix OHLCV into the U.S.-session SKHY series.

Because the U.S. listing is recent, the available U.S. research history may be materially shorter than the history of the underlying Korean company. Preserve that fact.

### USD

Verify that USD is the intended ProShares Ultra Semiconductors 2x ETF.

Do not substitute another leveraged ETF.

### MU / AMD / SMH / SPY

Verify ticker identity through Massive reference metadata where practical and record the instrument identity in the manifest.

## Dataset manifest

The repository currently recognizes:

- `SYNTHETIC_SAMPLE_FIXTURE`
- `REAL_HISTORICAL_UNVERIFIED_SOURCE`
- `REAL_HISTORICAL_VERIFIED`

Only the final status may enter historical research.

The Massive ingestion process must create a manifest containing at least:

```json
{
  "dataset_id": "massive_stocks_1m_<immutable-id>",
  "data_status": "REAL_HISTORICAL_VERIFIED",
  "provider": "Massive",
  "is_verified_market_data": true,
  "source_description": "Massive Stocks REST custom bars, 1-minute, split-adjusted, U.S. regular session",
  "license_or_citation": "https://www.massive.com/docs/rest/stocks/aggregates/custom-bars",
  "bar_resolution": "1m",
  "source_timezone": "America/New_York",
  "output_timezone": "UTC",
  "adjustment_status": "split_adjusted",
  "regular_session_only": true,
  "symbols": ["MU", "SNDK", "SKHY", "AMD", "USD", "SMH", "SPY"]
}
```

Also record:

- requested start/end;
- per-symbol actual start/end;
- per-symbol row count;
- per-symbol SHA-256;
- aggregate dataset hash;
- Massive endpoint;
- request parameters excluding the API key;
- importer git commit;
- acquisition timestamp in UTC;
- verification checks and outcomes;
- coverage/missing-minute diagnostics;
- symbol-history caveats.

Do not write the API key or any credential-derived token into the manifest.

## Manifest / loader integration

The existing `CsvEquityDataProvider` and `DatasetManifest` are already the authoritative loading path.

Prefer extending them rather than adding a parallel data-loading architecture.

The ingestion work may add:

- a Massive-specific acquisition module;
- manifest fields required for provenance;
- provider/adjustment propagation from the manifest into `DataProvenance`;
- a verification report;
- tests.

Do not bypass `load_historical_universe()`.

## CLI requirements

Add a deterministic local command such as:

```powershell
.un.ps1 ingest-massive -Start YYYY-MM-DD -End YYYY-MM-DD
```

The command must:

1. require `MASSIVE_API_KEY`;
2. fail immediately if the key is missing;
3. download all seven symbols;
4. write the CSVs to `data/processed`;
5. build/update the manifest;
6. run validation;
7. produce a machine-readable acquisition/verification report;
8. return non-zero on any failed verification;
9. never invoke a backtest automatically.

Also provide a direct Python CLI for debugging, but keep `run.ps1` as the canonical Windows path.

## Testing requirements

Do not make CI depend on Massive credentials or network access.

Add mocked/unit tests for:

- response parsing;
- pagination;
- timestamp conversion;
- RTH filtering;
- duplicate detection;
- malformed response rejection;
- rate-limit retry behavior;
- failed request behavior;
- stable CSV serialization;
- manifest generation;
- hash generation;
- missing/invalid OHLC rejection;
- refusal to mark a partial dataset verified.

A small recorded fixture derived from a documented Massive response may be used for tests, but it must be clearly labeled as a **Massive API response fixture**, not research market data.

## Acceptance criteria

The ingestion slice is complete when:

1. `MASSIVE_API_KEY` is never stored in Git.
2. All seven symbols can be downloaded with the canonical command.
3. Output CSVs conform to the existing loader.
4. RTH/UTC semantics are explicit and tested.
5. No synthetic bars are inserted.
6. Pagination is handled.
7. SHA-256 hashes are recorded.
8. The manifest contains full provenance.
9. `doctor-data` passes against the acquired dataset.
10. The verified-data gate accepts the dataset only after all required checks pass.
11. Missing or malformed data produces non-zero exit status.
12. Existing pytest and ruff remain green.
13. No strategy logic or research parameters were changed.
14. No historical backtest is run as part of ingestion.
15. The resulting dataset is usable by `comparison-historical` without a second conversion step.
