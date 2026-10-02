import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Literal, Protocol

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from tactical_engine.data.models import Bar
from tactical_engine.data.validation import validate_symbol_bars


class HistoricalDataMissingError(Exception):
    """Raised when required historical data files or symbols are missing."""

    pass


class DatasetVerificationError(ValueError):
    """Raised when historical research dataset fails the verified-data gate."""

    pass


class DatasetManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    dataset_id: str
    data_status: Literal[
        "SYNTHETIC_SAMPLE_FIXTURE",
        "REAL_HISTORICAL_UNVERIFIED_SOURCE",
        "REAL_HISTORICAL_VERIFIED",
    ]
    provider: str
    is_verified_market_data: bool = False
    source_description: str = ""
    license_or_citation: str = ""
    bar_resolution: str = "1d"
    source_timezone: str = "UTC"
    output_timezone: str = "UTC"
    adjustment_status: str = "split_adjusted"
    regular_session_only: bool = True
    symbols: list[str] = Field(default_factory=list)
    requested_start: str | None = None
    requested_end: str | None = None
    acquired_at_utc: str | None = None
    importer_git_sha: str | None = None
    endpoint: str | None = None
    aggregate_data_hash: str | None = None
    symbol_metadata: dict[str, dict] = Field(default_factory=dict)
    request_parameters: dict = Field(default_factory=dict)
    instrument_history_caveats: dict[str, str] = Field(default_factory=dict)
    verification: dict = Field(default_factory=dict)



def assert_research_dataset_verified(
    dataset_manifest: DatasetManifest | None,
    config: object = None,
) -> None:
    """Authoritative gate ensuring only REAL_HISTORICAL_VERIFIED datasets enter research.

    Rejects:
    - missing manifest
    - SYNTHETIC_SAMPLE_FIXTURE
    - REAL_HISTORICAL_UNVERIFIED_SOURCE
    - REAL_HISTORICAL_VERIFIED with is_verified_market_data != True
    - manifest bar resolution conflicting with loaded configuration
    - missing required identity/provenance fields per DATA_CONTRACT.md
    """
    if dataset_manifest is None:
        raise DatasetVerificationError(
            "Dataset manifest is missing. Historical research requires an explicit "
            "verified dataset manifest."
        )

    if dataset_manifest.data_status != "REAL_HISTORICAL_VERIFIED":
        raise DatasetVerificationError(
            f"Dataset status is '{dataset_manifest.data_status}'. Only 'REAL_HISTORICAL_VERIFIED' "
            "datasets are permitted for historical research execution."
        )

    if not dataset_manifest.is_verified_market_data:
        raise DatasetVerificationError(
            "Dataset is not certified as verified market data (is_verified_market_data=False). "
            "Historical research requires genuine verified market data."
        )

    if not dataset_manifest.dataset_id or not dataset_manifest.provider:
        raise DatasetVerificationError(
            "Dataset manifest is missing required provider/dataset_id identity fields "
            "per DATA_CONTRACT.md."
        )

    if config is not None and hasattr(config, "strategy"):
        strat_interval = getattr(config.strategy, "bar_interval", None)
        if strat_interval and dataset_manifest.bar_resolution != strat_interval:
            raise DatasetVerificationError(
                f"Manifest bar resolution '{dataset_manifest.bar_resolution}' does not match "
                f"configuration resolution '{strat_interval}'."
            )


def load_dataset_manifest(data_dir: Path | str) -> DatasetManifest:
    manifest_path = Path(data_dir) / "dataset_manifest.json"
    if manifest_path.is_file():
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
        return DatasetManifest.model_validate(data)

    return DatasetManifest(
        dataset_id=Path(data_dir).name,
        data_status="REAL_HISTORICAL_UNVERIFIED_SOURCE",
        provider="unverified_local_files",
        is_verified_market_data=False,
        source_description=(
            "No dataset_manifest.json found; unverified local CSV files "
            "without cryptographic source proof."
        ),
    )


class DataProvenance(BaseModel, frozen=True):
    symbol: str
    provider: str
    file_path: str
    file_sha256: str
    row_count: int
    start_time: datetime
    end_time: datetime
    resolution: str = "1d"
    timezone: str = "UTC"
    adjustment_status: str = "split_adjusted"


class UniverseHistoricalDataset(BaseModel):
    bars_by_symbol: dict[str, list[Bar]]
    provenance_by_symbol: dict[str, DataProvenance]
    aggregate_data_hash: str
    symbols: list[str] = Field(default_factory=list)
    dataset_manifest: DatasetManifest = Field(
        default_factory=lambda: DatasetManifest(
            dataset_id="unspecified",
            data_status="REAL_HISTORICAL_UNVERIFIED_SOURCE",
            provider="unverified_local_files",
        )
    )


def compute_file_sha256(path: Path) -> str:
    """Calculate SHA256 hex digest for a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class HistoricalEquityDataProvider(Protocol):
    def load_bars(
        self, symbol: str, start: datetime | None = None, end: datetime | None = None
    ) -> list[Bar]: ...

    def get_provenance(self, symbol: str) -> DataProvenance: ...


class CsvEquityDataProvider:
    def __init__(
        self,
        data_dir: Path | str,
        resolution: str = "1d",
        adjustment_status: str = "split_adjusted",
        default_timezone: str = "UTC",
    ):
        self.data_dir = Path(data_dir)
        self.resolution = resolution
        self.default_timezone = default_timezone
        self._provenance_cache: dict[str, DataProvenance] = {}
        manifest = load_dataset_manifest(self.data_dir)
        self.provider_name = (
            manifest.provider if manifest.data_status == "REAL_HISTORICAL_VERIFIED" else "csv"
        )
        self.adjustment_status = (
            manifest.adjustment_status
            if manifest.data_status == "REAL_HISTORICAL_VERIFIED"
            else adjustment_status
        )

    def _find_symbol_file(self, symbol: str) -> Path:
        candidates = [
            self.data_dir / f"{symbol}.csv",
            self.data_dir / f"{symbol.lower()}.csv",
            self.data_dir / f"{symbol.upper()}.csv",
            self.data_dir / f"{symbol}_{self.resolution}.csv",
        ]
        for c in candidates:
            if c.is_file():
                return c
        raise HistoricalDataMissingError(
            f"Missing required historical CSV for symbol '{symbol}' in directory '{self.data_dir}'"
        )

    def load_bars(
        self, symbol: str, start: datetime | None = None, end: datetime | None = None
    ) -> list[Bar]:
        file_path = self._find_symbol_file(symbol)
        df = pd.read_csv(file_path)

        # Normalize column names to lowercase
        df.columns = [c.strip().lower() for c in df.columns]

        # Identify timestamp column
        time_col = None
        for col in ["timestamp", "date", "datetime", "time"]:
            if col in df.columns:
                time_col = col
                break
        if not time_col:
            raise ValueError(
                f"No timestamp column found in {file_path}. Columns: {list(df.columns)}"
            )

        # Convert to datetime with UTC timezone
        df[time_col] = pd.to_datetime(df[time_col], utc=True)
        df = df.sort_values(by=time_col).reset_index(drop=True)

        # Check required OHLC columns
        required_cols = ["open", "high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column '{col}' in {file_path}")

        vol_col = "volume" if "volume" in df.columns else None
        vwap_col = "vwap" if "vwap" in df.columns else None

        bars: list[Bar] = []
        for _, row in df.iterrows():
            ts = row[time_col].to_pydatetime()
            if start and ts < start:
                continue
            if end and ts > end:
                continue

            vol = float(row[vol_col]) if vol_col and pd.notna(row[vol_col]) else 0.0
            vwap_val = float(row[vwap_col]) if vwap_col and pd.notna(row[vwap_col]) else None

            bars.append(
                Bar(
                    symbol=symbol.upper(),
                    timestamp=ts,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=vol,
                    vwap=vwap_val,
                    provider="csv",
                    adjustment_status=self.adjustment_status,
                )
            )

        if not bars:
            raise HistoricalDataMissingError(
                f"No bars loaded for symbol '{symbol}' in {file_path} within requested date range"
            )

        # Cache provenance
        file_sha = compute_file_sha256(file_path)
        prov = DataProvenance(
            symbol=symbol.upper(),
            provider=self.provider_name,
            file_path=str(file_path),
            file_sha256=file_sha,
            row_count=len(bars),
            start_time=bars[0].timestamp,
            end_time=bars[-1].timestamp,
            resolution=self.resolution,
            timezone="UTC",
            adjustment_status=self.adjustment_status,
        )
        self._provenance_cache[symbol.upper()] = prov
        return bars

    def get_provenance(self, symbol: str) -> DataProvenance:
        sym = symbol.upper()
        if sym in self._provenance_cache:
            return self._provenance_cache[sym]
        # Load bars to populate provenance
        self.load_bars(sym)
        return self._provenance_cache[sym]


def load_historical_universe(
    data_dir: Path | str,
    symbols: list[str],
    resolution: str = "1d",
    adjustment_status: str = "split_adjusted",
    start: datetime | None = None,
    end: datetime | None = None,
) -> UniverseHistoricalDataset:
    """Load historical bars for a full universe, validating data integrity and provenance."""
    provider = CsvEquityDataProvider(
        data_dir=data_dir,
        resolution=resolution,
        adjustment_status=adjustment_status,
    )

    bars_by_symbol: dict[str, list[Bar]] = {}
    provenance_by_symbol: dict[str, DataProvenance] = {}
    hash_agg = hashlib.sha256()

    for sym in symbols:
        sym_upper = sym.upper()
        bars = provider.load_bars(sym_upper, start=start, end=end)
        validation_res = validate_symbol_bars(
            sym_upper, bars, expected_interval=resolution
        )
        if not validation_res.is_valid:
            raise ValueError(
                f"Historical data validation failed for symbol '{sym_upper}': "
                f"{validation_res.errors}"
            )
        bars_by_symbol[sym_upper] = bars
        prov = provider.get_provenance(sym_upper)
        provenance_by_symbol[sym_upper] = prov
        hash_agg.update(f"{sym_upper}:{prov.file_sha256}:{prov.row_count}".encode())

    manifest = load_dataset_manifest(data_dir)

    return UniverseHistoricalDataset(
        bars_by_symbol=bars_by_symbol,
        provenance_by_symbol=provenance_by_symbol,
        aggregate_data_hash=hash_agg.hexdigest(),
        symbols=[s.upper() for s in symbols],
        dataset_manifest=manifest,
    )
