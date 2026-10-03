import json
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class InstrumentEvidenceStatus(StrEnum):
    SOURCE_IDENTIFIED = "SOURCE_IDENTIFIED"
    CANDIDATE_PROXY = "CANDIDATE_PROXY"
    OUT_OF_SCOPE_FOR_V2 = "OUT_OF_SCOPE_FOR_V2"


class InstrumentDataProviderStatus(StrEnum):
    VALIDATED = "VALIDATED"
    PARTIALLY_VALIDATED = "PARTIALLY_VALIDATED"
    UNVALIDATED = "UNVALIDATED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class V2InstrumentEntry(BaseModel):
    ticker: str
    name: str
    issuer: str
    instrument_type: str
    underlying: str
    leverage: float = 1.0
    direction: str = "LONG"
    exchange_venue: str
    inception_listing_date: str | None = None
    source_evidence_status: InstrumentEvidenceStatus
    data_provider_status: InstrumentDataProviderStatus
    first_valid_bar: str | None = None
    coverage_pct: float = 0.0
    liquidity_notes: str = ""
    dr_ratio: str | None = None
    notes: str = ""


class V2InstrumentManifest(BaseModel):
    manifest_name: str = "reddit_behavioral_v2_us_instrument_manifest"
    version: str = "2.0.0"
    created_at_utc: str
    market_scope: str = "US_MARKET_ONLY"
    direct_asia_replication_status: str = "OUT_OF_SCOPE_FOR_V2"
    instruments: list[V2InstrumentEntry] = Field(default_factory=list)

    def get_source_identified_symbols(self) -> list[str]:
        """Return list of tickers that are directly observed/named by primary source."""
        return [
            inst.ticker
            for inst in self.instruments
            if inst.source_evidence_status == InstrumentEvidenceStatus.SOURCE_IDENTIFIED
        ]

    def get_candidate_proxy_symbols(self) -> list[str]:
        """Return list of tickers that are candidate U.S. proxies."""
        return [
            inst.ticker
            for inst in self.instruments
            if inst.source_evidence_status == InstrumentEvidenceStatus.CANDIDATE_PROXY
        ]

    def get_excluded_asia_symbols(self) -> list[str]:
        """Return list of direct Asian exchange symbols strictly out of scope for V2."""
        return [
            inst.ticker
            for inst in self.instruments
            if inst.source_evidence_status == InstrumentEvidenceStatus.OUT_OF_SCOPE_FOR_V2
        ]

    def get_instrument(self, ticker: str) -> V2InstrumentEntry | None:
        """Find instrument entry by ticker."""
        ticker_up = ticker.upper()
        for inst in self.instruments:
            if inst.ticker.upper() == ticker_up:
                return inst
        return None

    def is_asia_direct_excluded(self, ticker: str) -> bool:
        """Check if symbol is an excluded direct Asian exchange instrument."""
        inst = self.get_instrument(ticker)
        if inst:
            return inst.source_evidence_status == InstrumentEvidenceStatus.OUT_OF_SCOPE_FOR_V2
        return ticker.upper() in ("000660.KS", "285A.T", "000660", "285A")


def load_v2_instrument_manifest(manifest_path: Path | str | None = None) -> V2InstrumentManifest:
    """Load and validate the V2 U.S. instrument manifest JSON."""
    if manifest_path is None:
        manifest_path = Path("reports/data_manifests/v2_us_instrument_manifest.json")
    p = Path(manifest_path)
    if not p.exists():
        raise FileNotFoundError(f"V2 Instrument Manifest not found at: {p}")
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    return V2InstrumentManifest.model_validate(data)
