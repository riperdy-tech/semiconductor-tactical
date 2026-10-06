from datetime import UTC, datetime

import pytest

from tactical_engine.options.data import (
    OptionDataManifest,
    OptionDataStatus,
    normalize_cbbo_1m_row,
    parse_cbbo_1m_rows,
    validate_option_quotes,
)


def test_cbbo_row_normalization_uses_explicit_underlying_price():
    timestamp = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    row = {
        "ts_event": timestamp,
        "symbol": "MU261016C00105000",
        "underlying": "MU",
        "call_put": "C",
        "strike_price": 105.0,
        "expiration": datetime(2026, 10, 16, 20, 0, tzinfo=UTC),
        "bid_px": 2.00,
        "ask_px": 2.20,
    }

    quote = normalize_cbbo_1m_row(row, underlying_price=101.0)
    assert quote.bid == 2.0
    assert quote.ask == 2.2
    assert quote.underlying_price == 101.0


def test_cbbo_parser_requires_exact_timestamp_matched_underlying():
    timestamp = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    row = {
        "ts_event": timestamp,
        "symbol": "MU261016C00105000",
        "underlying": "MU",
        "call_put": "C",
        "strike_price": 105.0,
        "expiration": datetime(2026, 10, 16, 20, 0, tzinfo=UTC),
        "bid_px": 2.00,
        "ask_px": 2.20,
    }

    with pytest.raises(ValueError, match="Missing synchronized underlying price"):
        parse_cbbo_1m_rows([row], underlying_prices={})


def test_manifest_cannot_claim_validated_without_provenance():
    manifest = OptionDataManifest(status=OptionDataStatus.GATED_UNVALIDATED)
    manifest.validate_for_status()

    invalid = OptionDataManifest(
        status=OptionDataStatus.VALIDATED,
        source_vendor="Databento",
        product="OPRA.PILLAR",
    )
    with pytest.raises(ValueError, match="validated status"):
        invalid.validate_for_status()


def test_quote_quality_is_deterministic():
    timestamp = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    row = {
        "ts_event": timestamp,
        "symbol": "MU261016C00105000",
        "underlying": "MU",
        "call_put": "C",
        "strike_price": 105.0,
        "expiration": datetime(2026, 10, 16, 20, 0, tzinfo=UTC),
        "bid_px": 2.00,
        "ask_px": 2.20,
    }
    quote = normalize_cbbo_1m_row(row, underlying_price=101.0)
    quality = validate_option_quotes([quote])
    assert quality["verification"] == "PASS"
    assert quality["row_count"] == 1
    assert quality["contract_count"] == 1
