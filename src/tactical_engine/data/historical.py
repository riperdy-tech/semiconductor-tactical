import hashlib
from datetime import datetime
from pathlib import Path
from typing import Protocol

import pandas as pd
from pydantic import BaseModel, Field

from tactical_engine.data.models import Bar
from tactical_engine.data.validation import validate_symbol_bars


class HistoricalDataMissingError(Exception):
    """Raised when required historical data files or symbols are missing."""

    pass


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
        self.adjustment_status = adjustment_status
        self.default_timezone = default_timezone
        self._provenance_cache: dict[str, DataProvenance] = {}

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
            provider="csv",
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

    return UniverseHistoricalDataset(
        bars_by_symbol=bars_by_symbol,
        provenance_by_symbol=provenance_by_symbol,
        aggregate_data_hash=hash_agg.hexdigest(),
        symbols=[s.upper() for s in symbols],
    )
