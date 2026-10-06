"""Provider-neutral ingestion and provenance validation for V2-D option data.

The headline research path requires authentic point-in-time bid/ask quotes.
This module only normalizes already-acquired records; it does not download
market data and it does not synthesize prices or Greeks.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from tactical_engine.options.contracts import OptionContractType, OptionQuote


class OptionDataStatus(StrEnum):
    GATED_UNVALIDATED = "GATED_UNVALIDATED"
    VALIDATED_PARTIAL = "VALIDATED_PARTIAL"
    VALIDATED = "VALIDATED"


class OptionDataManifest(BaseModel, frozen=True):
    manifest_version: str = "v2d-1"
    status: OptionDataStatus = OptionDataStatus.GATED_UNVALIDATED
    source_vendor: str | None = None
    product: str | None = None
    license_usage_status: str | None = None
    retrieval_timestamp_utc: datetime | None = None
    underlying_symbols: list[str] = Field(default_factory=list)
    start_timestamp_utc: datetime | None = None
    end_timestamp_utc: datetime | None = None
    quote_resolution: str | None = None
    timestamp_precision: str | None = None
    option_symbology: str | None = None
    strike_range: str | None = None
    expiration_coverage: str | None = None
    bid_ask_completeness: str | None = None
    volume_open_interest: str | None = None
    delta_availability: str | None = None
    underlying_price_source: str | None = None
    corporate_action_source: str | None = None
    per_file_sha256: dict[str, str] = Field(default_factory=dict)
    aggregate_sha256: str | None = None
    structural_validation: dict[str, Any] = Field(default_factory=dict)

    def validate_for_status(self) -> None:
        if self.status == OptionDataStatus.GATED_UNVALIDATED:
            return

        required = {
            "source_vendor": self.source_vendor,
            "product": self.product,
            "license_usage_status": self.license_usage_status,
            "retrieval_timestamp_utc": self.retrieval_timestamp_utc,
            "underlying_symbols": self.underlying_symbols,
            "start_timestamp_utc": self.start_timestamp_utc,
            "end_timestamp_utc": self.end_timestamp_utc,
            "quote_resolution": self.quote_resolution,
            "timestamp_precision": self.timestamp_precision,
            "option_symbology": self.option_symbology,
            "bid_ask_completeness": self.bid_ask_completeness,
            "underlying_price_source": self.underlying_price_source,
            "per_file_sha256": self.per_file_sha256,
            "aggregate_sha256": self.aggregate_sha256,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(
                "Option manifest cannot claim validated status with missing fields: "
                + ", ".join(sorted(missing))
            )


def _value(record: object, *names: str) -> Any:
    if isinstance(record, Mapping):
        for name in names:
            if name in record:
                return record[name]
        return None

    for name in names:
        if hasattr(record, name):
            return getattr(record, name)
    return None


def _datetime_utc(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError(f"Invalid {field_name} timestamp: {value!r}") from exc
    elif isinstance(value, int | float):
        number = float(value)
        if number > 1e17:
            dt = datetime.fromtimestamp(number / 1e9, tz=UTC)
        elif number > 1e14:
            dt = datetime.fromtimestamp(number / 1e6, tz=UTC)
        elif number > 1e11:
            dt = datetime.fromtimestamp(number / 1e3, tz=UTC)
        else:
            dt = datetime.fromtimestamp(number, tz=UTC)
    else:
        raise ValueError(f"Missing or unsupported {field_name} timestamp")

    if dt.tzinfo is None:
        raise ValueError(f"{field_name} timestamp must include timezone information")
    return dt.astimezone(UTC)


def _contract_type(value: Any) -> OptionContractType:
    normalized = str(value).strip().upper()
    if normalized in {"C", "CALL"}:
        return OptionContractType.CALL
    if normalized in {"P", "PUT"}:
        return OptionContractType.PUT
    raise ValueError(f"Unsupported option contract type: {value!r}")


def normalize_cbbo_1m_row(
    record: object,
    *,
    underlying_price: float,
) -> OptionQuote:
    """Normalize one cbbo-1m-like record into an executable OptionQuote.

    The caller must supply an underlying price synchronized to the quote
    timestamp. The adapter does not infer that price from future bars or
    calculate a theoretical option value.
    """

    symbol = _value(record, "symbol", "raw_symbol", "contract_symbol")
    underlying = _value(record, "underlying", "underlying_ticker", "parent_symbol")
    timestamp = _datetime_utc(_value(record, "ts_event", "timestamp"), "quote")
    expiration = _datetime_utc(
        _value(record, "expiration", "expiration_ts", "expiration_timestamp"),
        "expiration",
    )
    contract_type = _contract_type(
        _value(record, "call_put", "put_call", "contract_type")
    )
    strike = _value(record, "strike_price", "strike")
    bid = _value(record, "bid_px", "bid_price", "bid")
    ask = _value(record, "ask_px", "ask_price", "ask")
    if any(value is None for value in (symbol, underlying, strike, bid, ask)):
        raise ValueError("cbbo-1m record is missing required contract/quote fields")

    return OptionQuote(
        symbol=str(symbol),
        underlying=str(underlying),
        timestamp=timestamp,
        contract_type=contract_type,
        strike=float(strike),
        expiration=expiration,
        bid=float(bid),
        ask=float(ask),
        underlying_price=float(underlying_price),
        volume=float(_value(record, "volume", "traded_volume") or 0.0),
        open_interest=float(_value(record, "open_interest") or 0.0),
        contract_multiplier=int(_value(record, "contract_multiplier", "multiplier") or 100),
        bid_size=float(_value(record, "bid_sz", "bid_size") or 0.0),
        ask_size=float(_value(record, "ask_sz", "ask_size") or 0.0),
        last=(
            float(last)
            if (last := _value(record, "last", "last_price")) is not None
            else None
        ),
        quote_condition=(
            str(condition)
            if (condition := _value(record, "quote_condition", "condition")) is not None
            else None
        ),
    )


def parse_cbbo_1m_rows(
    rows: Iterable[object],
    *,
    underlying_prices: Mapping[tuple[str, datetime], float],
) -> list[OptionQuote]:
    """Parse rows while requiring an exact timestamp-matched underlying price.

    Missing synchronized underlying prices are a hard data-quality error. This
    prevents the parser from silently using a later or earlier market price.
    """

    quotes: list[OptionQuote] = []
    seen: set[tuple[str, str, datetime]] = set()

    for row in rows:
        raw_underlying = _value(row, "underlying", "underlying_ticker", "parent_symbol")
        if raw_underlying is None:
            raise ValueError("cbbo-1m record is missing underlying symbol")
        timestamp = _datetime_utc(_value(row, "ts_event", "timestamp"), "quote")
        key = (str(raw_underlying), timestamp)
        underlying_price = underlying_prices.get(key)
        if underlying_price is None:
            raise ValueError(
                "Missing synchronized underlying price for "
                f"{raw_underlying} at {timestamp.isoformat()}"
            )

        quote = normalize_cbbo_1m_row(row, underlying_price=float(underlying_price))
        quote_key = (quote.underlying, quote.symbol, quote.timestamp)
        if quote_key in seen:
            raise ValueError(
                f"Duplicate option quote for {quote.symbol} at {quote.timestamp.isoformat()}"
            )
        seen.add(quote_key)
        quotes.append(quote)

    quotes.sort(key=lambda q: (q.underlying, q.symbol, q.timestamp))
    return quotes


def validate_option_quotes(quotes: Iterable[OptionQuote]) -> dict[str, Any]:
    """Return deterministic structural quality statistics without changing rows."""

    rows = list(quotes)
    by_contract: dict[str, list[OptionQuote]] = {}
    for quote in rows:
        by_contract.setdefault(quote.symbol, []).append(quote)

    duplicate_timestamps = 0
    backwards_timestamps = 0
    invalid_spreads = 0

    for contract_rows in by_contract.values():
        sorted_rows = sorted(contract_rows, key=lambda q: q.timestamp)
        for index, quote in enumerate(sorted_rows):
            if quote.ask < quote.bid or quote.bid < 0 or quote.ask < 0:
                invalid_spreads += 1
            if index > 0 and quote.timestamp == sorted_rows[index - 1].timestamp:
                duplicate_timestamps += 1
            if index > 0 and quote.timestamp < sorted_rows[index - 1].timestamp:
                backwards_timestamps += 1

    return {
        "row_count": len(rows),
        "contract_count": len(by_contract),
        "duplicate_timestamps": duplicate_timestamps,
        "backwards_timestamps": backwards_timestamps,
        "invalid_spreads": invalid_spreads,
        "verification": (
            "PASS"
            if duplicate_timestamps == 0
            and backwards_timestamps == 0
            and invalid_spreads == 0
            else "FAIL"
        ),
    }
