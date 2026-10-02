# Gemini Handoff — Massive Data Acquisition

## Objective

Implement the Massive historical-market-data ingestion slice described by:

`docs/execution_plan/MASSIVE_DATA_INGESTION.md`

The human will provide a valid Massive API key at runtime.

Your job is to turn that key into a reproducible, verified local dataset that the **existing** historical research engine can consume.

This is a data-engineering task, not a strategy-optimization task.

## Read before coding

Read in this order:

1. `AGENTS.md`
2. `docs/REDDIT_SOURCE_NOTES.md`
3. `docs/DATA_CONTRACT.md`
4. `docs/BACKTEST_PROTOCOL.md`
5. `docs/DECISIONS.md`
6. `docs/execution_plan/DATA_ACQUISITION.md`
7. `docs/execution_plan/FINAL_GATE_FIX.md`
8. `configs/base.yaml`
9. `src/tactical_engine/data/historical.py`
10. `src/tactical_engine/data/validation.py`
11. `src/tactical_engine/data/doctor.py`

## Required implementation

Build a Massive ingestion path with:

- environment-based credential handling;
- 1-minute custom-bar download;
- pagination;
- retry/backoff;
- RTH-only filtering;
- UTC-normalized output;
- deterministic CSV serialization;
- SHA-256 hashing;
- manifest generation;
- verification diagnostics;
- unit tests with mocked HTTP;
- canonical Windows runner integration.

Preferred architecture:

```text
Massive REST API
      |
      v
src/tactical_engine/data/massive.py
      |
      v
data/raw/massive/        (optional raw responses; ignored by Git)
      |
      v
data/processed/*.csv
      |
      v
dataset_manifest.json
      |
      v
doctor-data
      |
      v
REAL_HISTORICAL_VERIFIED
      |
      v
comparison-historical
```

Do not create a second backtest data loader.

## Required universe

Download:

```text
MU
SNDK
SKHY
AMD
USD
SMH
SPY
```

The first five are the tradable universe. SMH/SPY are benchmark inputs.

## Credential handling

Use environment variable:

`MASSIVE_API_KEY`

The code must never log the value.

A missing key must cause a clear non-zero failure.

Never create or commit a real `.env` file.

## API details

Use Massive's documented custom stock bars endpoint:

`/v2/aggs/ticker/{ticker}/range/1/minute/{from}/{to}`

with:

- `adjusted=true`
- `sort=asc`
- high enough `limit` for the account;
- authentication via API key.

Massive documents a `next_url` pagination field. Follow it until the dataset is complete.

Do not assume one request returns everything.

Do not silently swallow empty/error responses.

## Timestamp handling

Massive documents aggregate timestamps in Eastern Time.

For each response:

1. interpret the source timestamp using the documented Massive ET convention;
2. convert to timezone-aware UTC;
3. filter regular U.S. session using the ET representation;
4. write the final timestamp in UTC.

Do not filter on naive UTC clock values.

Keep only regular session 09:30-16:00 America/New_York.

Do not include pre-market or after-hours observations in this research dataset.

Do not fill missing minute bars.

## Adjustment handling

Use `adjusted=true`.

Label the result `split_adjusted`.

Do not claim dividend-adjusted total returns.

Do not mix adjusted and unadjusted files.

## Output format

For every symbol write:

`data/processed/<SYMBOL>.csv`

Minimum columns:

```csv
timestamp,open,high,low,close,volume
```

Prefer:

```csv
timestamp,open,high,low,close,volume,vwap
```

Use deterministic ascending timestamp ordering.

Do not include API response-specific column names such as `t,c,o,h,l,v,vw` in the final repository CSV unless the loader is explicitly updated to accept them.

## Date-window handling

The importer must accept explicit start/end dates.

Do not bake in:

- `2026-07-01`;
- `2026-09-29`;
- `2026-10-02`;

as permanent strategy dates.

The 2026-09-29 post date and 90-day observation framing are source facts, not a license to alter the research period. Respect the actual boundaries stored in research configuration / decisions.

Fetch enough prior warm-up history for the configured lookback features.

## Data-quality policy

Fail the acquisition/verification if:

- any required file is missing;
- HTTP/API errors prevent complete coverage;
- JSON parsing fails;
- timestamps cannot be interpreted;
- duplicate timestamps remain;
- timestamps are not monotone;
- OHLC relationships fail;
- non-positive prices remain;
- negative volume remains;
- output is not 1-minute data;
- RTH filtering failed;
- the manifest is internally inconsistent.

Do not turn missing data into zeros or forward fills.

For ordinary trading-calendar gaps, do not fail merely because there is no overnight bar. Report them.

For intraday missing slots, calculate and report coverage and material gaps so they can be reviewed before verification.

## Symbol-specific controls

### SKHY

Confirm the file represents U.S.-listed Nasdaq SKHY.

Do not splice Korean exchange data into it.

Record its shorter U.S. history in the manifest.

### SNDK

Confirm the vendor's representation around the security's standalone listing/corporate-action history.

Do not assume ticker continuity.

### USD

Confirm the instrument is the intended 2x semiconductor ETF.

Do not substitute a different leveraged ETF.

### SMH/SPY

These are benchmark inputs only. They must never become tradable symbols in the backtest.

## Manifest

Keep the existing `dataset_manifest.json` mechanism authoritative.

Extend its schema only as needed to preserve all provenance requested by `MASSIVE_DATA_INGESTION.md`.

The final verified manifest must include:

- immutable dataset id;
- `REAL_HISTORICAL_VERIFIED`;
- `provider=Massive`;
- `is_verified_market_data=true`;
- source URL/product;
- 1m resolution;
- source timezone;
- output timezone;
- split-adjustment policy;
- RTH-only flag;
- requested and actual coverage;
- seven symbols;
- per-file row counts;
- per-file SHA-256;
- aggregate hash;
- acquisition timestamp;
- importer git SHA;
- request parameters excluding secrets;
- gap/coverage diagnostics;
- instrument/history caveats.

Never include the key.

## Canonical command

Extend `run.ps1` with something equivalent to:

```powershell
.un.ps1 ingest-massive -Start 2026-07-01 -End 2026-09-29
```

The dates above are an example only. Do not treat them as the authoritative research boundaries.

Required behavior:

- missing key -> non-zero;
- any acquisition failure -> non-zero;
- any validation failure -> non-zero;
- successful verified acquisition -> zero;
- no automatic backtest.

Also expose a direct Python command for development.

## CI

Network access and a real API key must not be required by CI.

Use mocked HTTP responses / local fixtures.

Add tests covering the critical transformations.

Do not add a real secret to GitHub Actions.

## Do not do

- Do not optimize strategy thresholds.
- Do not change pullback z-score.
- Do not change leverage.
- Do not change cost assumptions.
- Do not change OOS boundaries.
- Do not fabricate missing bars.
- Do not splice foreign-market data.
- Do not substitute proxies.
- Do not mark partial data verified.
- Do not run the final research interpretation yet.
- Do not add options to this task.
- Do not add live trading.
- Do not expose or persist the API key.

## Verification sequence after implementation

Run:

```powershell
.un.ps1 test
.un.ps1 doctor
```

Then, with the real key supplied locally:

```powershell
$env:MASSIVE_API_KEY = "<provided-key>"
.un.ps1 ingest-massive -Start <documented-start> -End <documented-end>
.un.ps1 doctor-data -Config configs/base.yaml -DataDir data/processed
```

The ingestion command should print a concise table showing:

- symbol;
- rows;
- actual start/end;
- RTH coverage;
- missing-minute diagnostics;
- SHA-256 prefix;
- verification status.

Only after the data is independently verified should the human run:

```powershell
.un.ps1 comparison-historical -Config configs/base.yaml -DataDir data/processed
```

If the final gate fix has not yet been implemented, finish that separately before declaring the historical command correct.

## Definition of done

Software:

- tests pass;
- ruff passes;
- CI passes;
- ingestion command exists;
- importer is deterministic;
- credentials are safe;
- manifest is complete;
- verification is strict;
- historical research still refuses unverified data.

Data:

- all seven symbols downloaded from Massive;
- all seven files validate;
- manifest is generated;
- hashes are recorded;
- the verified-data gate accepts only after all checks pass.

Research:

- do not claim an edge merely because the files downloaded;
- do not optimize based on the first backtest;
- leave the interpretation to the research phase.
