# Massive Dataset Manifest Schema

## Purpose

This file defines the provenance information that should accompany the local Massive-derived dataset.

The actual market-data files are intentionally excluded from Git by the repository's current `.gitignore`.

The manifest is the audit record.

## Minimum manifest

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
  "symbols": [
    "MU",
    "SNDK",
    "SKHY",
    "AMD",
    "USD",
    "SMH",
    "SPY"
  ],
  "requested_start": "YYYY-MM-DD",
  "requested_end": "YYYY-MM-DD",
  "acquired_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "importer_git_sha": "<git-sha>",
  "endpoint": "https://api.massive.com/v2/aggs/ticker/{ticker}/range/1/minute/{from}/{to}"
}
```

## Recommended per-symbol evidence

```json
{
  "symbol_metadata": {
    "MU": {
      "row_count": 0,
      "actual_start": "YYYY-MM-DDTHH:MM:SSZ",
      "actual_end": "YYYY-MM-DDTHH:MM:SSZ",
      "sha256": "<sha256>",
      "rth_coverage_ratio": 0.0,
      "missing_minute_slots": 0,
      "large_intraday_gaps": 0,
      "verification": "PASS"
    }
  }
}
```

## Request parameters

Record the request parameters that determine research data semantics, but never record the secret:

```json
{
  "request_parameters": {
    "multiplier": 1,
    "timespan": "minute",
    "adjusted": true,
    "sort": "asc",
    "session_filter": "09:30-16:00 America/New_York",
    "output_timezone": "UTC"
  }
}
```

Never include:

- API key;
- Authorization header;
- cookies;
- access tokens;
- credential-derived signatures.

## Dataset-level hash

Record:

```json
{
  "aggregate_data_hash": "<sha256>"
}
```

The aggregate hash must be deterministic from the ordered symbol/file hashes and enough dataset identity to prevent accidental mixing of files from different acquisitions.

## History caveats

Use an explicit field:

```json
{
  "instrument_history_caveats": {
    "SNDK": "<documented vendor/ticker-history treatment>",
    "SKHY": "<U.S.-listing history and coverage limitation>",
    "USD": "<instrument identity verification>"
  }
}
```

Do not silently write a caveat into prose only.

## Verification record

Record the exact checks performed:

```json
{
  "verification": {
    "required_symbols_present": true,
    "all_files_parse": true,
    "timestamps_utc": true,
    "monotonic": true,
    "duplicates": false,
    "ohlc_valid": true,
    "positive_prices": true,
    "nonnegative_volume": true,
    "rth_only": true,
    "resolution_1m": true,
    "corporate_action_policy_documented": true,
    "per_file_hashes_present": true,
    "provider_documented": true,
    "status": "PASS"
  }
}
```

A dataset may not be marked `REAL_HISTORICAL_VERIFIED` when any mandatory verification field is false.

## Retention

The final manifest should remain available even when raw data files are omitted from Git.

Recommended locations:

- local canonical: `data/processed/dataset_manifest.json`;
- generated evidence copy: `reports/data_manifests/<dataset_id>.json`.

Do not put large market-data CSVs in Git simply to preserve provenance.

## Relationship to code

The manifest complements, not replaces:

- `docs/DATA_CONTRACT.md`;
- `DatasetManifest`;
- `DataProvenance`;
- `load_historical_universe()`;
- `assert_research_dataset_verified()`.

The code should derive runtime provenance from the manifest rather than inferring source identity from filenames or directories.
