"""Unit tests for Massive historical market data acquisition, RTH filtering, and manifest.

All tests use mocked responses or local fixtures so network access and API credentials
are never required by CI.
"""

from __future__ import annotations

import io
import json
import urllib.error
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tactical_engine.config import EngineConfig
from tactical_engine.data.historical import (
    assert_research_dataset_verified,
    load_dataset_manifest,
)
from tactical_engine.data.massive import (
    MassiveClient,
    MassiveCredentialsError,
    compute_file_sha256,
    filter_and_convert_bars,
    get_massive_api_key,
    ingest_massive_universe,
    save_symbol_csv,
    validate_converted_bars,
)


def test_get_massive_api_key(monkeypatch, tmp_path):
    # Case 1: Present in environment
    monkeypatch.setenv("MASSIVE_API_KEY", "test_key_123")
    assert get_massive_api_key() == "test_key_123"

    # Case 2: Missing from environment and no .env
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
    with patch("pathlib.Path.is_file", return_value=False):
        with pytest.raises(MassiveCredentialsError):
            get_massive_api_key()


def test_filter_and_convert_bars_rth_filtering():
    """Verify that only regular U.S. trading session (09:30-16:00 ET) on weekdays is retained."""
    raw_bars = [
        # 12:00 UTC = 08:00 ET (Pre-market -> FILTER OUT)
        {
            "t": int(datetime(2026, 7, 15, 12, 0, tzinfo=UTC).timestamp() * 1000),
            "o": 100,
            "h": 101,
            "l": 99,
            "c": 100.5,
            "v": 1000,
            "vw": 100.2,
        },
        # 13:29 UTC = 09:29 ET (Pre-market -> FILTER OUT)
        {
            "t": int(datetime(2026, 7, 15, 13, 29, tzinfo=UTC).timestamp() * 1000),
            "o": 100.5,
            "h": 101,
            "l": 100,
            "c": 100.8,
            "v": 1200,
            "vw": 100.6,
        },
        # 13:30 UTC = 09:30 ET (RTH start -> RETAIN)
        {
            "t": int(datetime(2026, 7, 15, 13, 30, tzinfo=UTC).timestamp() * 1000),
            "o": 101,
            "h": 102,
            "l": 100.5,
            "c": 101.5,
            "v": 5000,
            "vw": 101.2,
        },
        # 16:00 UTC = 12:00 ET (RTH -> RETAIN)
        {
            "t": int(datetime(2026, 7, 15, 16, 0, tzinfo=UTC).timestamp() * 1000),
            "o": 102,
            "h": 103,
            "l": 101.5,
            "c": 102.5,
            "v": 4000,
            "vw": 102.1,
        },
        # 19:59 UTC = 15:59 ET (RTH last bar -> RETAIN)
        {
            "t": int(datetime(2026, 7, 15, 19, 59, tzinfo=UTC).timestamp() * 1000),
            "o": 103,
            "h": 103.5,
            "l": 102.8,
            "c": 103.2,
            "v": 6000,
            "vw": 103.0,
        },
        # 20:00 UTC = 16:00 ET (Post-market -> FILTER OUT)
        {
            "t": int(datetime(2026, 7, 15, 20, 0, tzinfo=UTC).timestamp() * 1000),
            "o": 103.2,
            "h": 103.3,
            "l": 103.0,
            "c": 103.1,
            "v": 500,
            "vw": 103.1,
        },
        # Saturday 2026-07-18 13:30 UTC -> Weekend (FILTER OUT)
        {
            "t": int(datetime(2026, 7, 18, 13, 30, tzinfo=UTC).timestamp() * 1000),
            "o": 103,
            "h": 103.5,
            "l": 102.8,
            "c": 103.2,
            "v": 100,
            "vw": 103.0,
        },
    ]

    converted = filter_and_convert_bars(raw_bars, "MU")
    # Only 3 bars should be retained: 09:30, 12:00, 15:59 ET
    assert len(converted) == 3
    assert converted[0]["timestamp"] == "2026-07-15T13:30:00Z"
    assert converted[1]["timestamp"] == "2026-07-15T16:00:00Z"
    assert converted[2]["timestamp"] == "2026-07-15T19:59:00Z"

    assert converted[0]["open"] == 101.0
    assert converted[0]["close"] == 101.5
    assert converted[0]["volume"] == 5000.0
    assert converted[0]["vwap"] == 101.2


def test_validate_converted_bars_valid_and_invalid():
    t0 = datetime(2026, 7, 15, 13, 30, tzinfo=UTC)
    valid_bars = [
        {
            "timestamp": "2026-07-15T13:30:00Z",
            "datetime_utc": t0,
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "volume": 1000.0,
            "vwap": 100.5,
        },
        {
            "timestamp": "2026-07-15T13:31:00Z",
            "datetime_utc": datetime(2026, 7, 15, 13, 31, tzinfo=UTC),
            "open": 101.0,
            "high": 103.0,
            "low": 100.5,
            "close": 102.0,
            "volume": 1200.0,
            "vwap": 101.8,
        },
    ]
    res_valid = validate_converted_bars(valid_bars, "MU")
    assert res_valid["verification"] == "PASS"
    assert res_valid["row_count"] == 2
    assert res_valid["missing_minute_slots"] == 0

    # Non-positive price
    invalid_price = [dict(valid_bars[0], close=-1.0)]
    res_inv1 = validate_converted_bars(invalid_price, "MU")
    assert res_inv1["verification"] == "FAIL"

    # Low > Open violation
    invalid_ohlc = [dict(valid_bars[0], low=105.0)]
    res_inv2 = validate_converted_bars(invalid_ohlc, "MU")
    assert res_inv2["verification"] == "FAIL"

    # Non-monotonic timestamp
    inv_mono = [
        valid_bars[1],
        dict(valid_bars[0], datetime_utc=datetime(2026, 7, 15, 13, 29, tzinfo=UTC)),
    ]
    res_inv3 = validate_converted_bars(inv_mono, "MU")
    assert res_inv3["verification"] == "FAIL"


def test_save_symbol_csv_and_sha256(tmp_path: Path):
    t0 = datetime(2026, 7, 15, 13, 30, tzinfo=UTC)
    bars = [
        {
            "timestamp": "2026-07-15T13:30:00Z",
            "datetime_utc": t0,
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "volume": 1000.0,
            "vwap": 100.5,
        }
    ]
    csv_file = tmp_path / "MU.csv"
    sha = save_symbol_csv(bars, csv_file)
    assert csv_file.exists()
    assert sha == compute_file_sha256(csv_file)

    content = csv_file.read_text(encoding="utf-8")
    assert content.startswith("timestamp,open,high,low,close,volume,vwap\n")
    assert "2026-07-15T13:30:00Z,100.0000,102.0000,99.0000,101.0000,1000,100.5000\n" in content


def test_massive_client_pagination_mocked():
    client = MassiveClient(api_key="test_secret")

    page1 = {
        "status": "OK",
        "results": [{"t": 1784102400000, "o": 100, "h": 101, "l": 99, "c": 100.5, "v": 1000}],
        "next_url": "https://api.massive.com/v2/aggs/ticker/MU/range/1/minute/page2",
    }
    page2 = {
        "status": "OK",
        "results": [{"t": 1784102460000, "o": 100.5, "h": 102, "l": 100, "c": 101.5, "v": 1200}],
        "next_url": None,
    }

    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = json.dumps(page1).encode("utf-8")
    mock_resp1.__enter__.return_value = mock_resp1

    mock_resp2 = MagicMock()
    mock_resp2.read.return_value = json.dumps(page2).encode("utf-8")
    mock_resp2.__enter__.return_value = mock_resp2

    with patch("urllib.request.urlopen", side_effect=[mock_resp1, mock_resp2]) as mock_open:
        results = client.fetch_custom_bars("MU", "2026-07-15", "2026-07-15")
        assert len(results) == 2
        assert mock_open.call_count == 2


def test_massive_client_429_retry_mocked():
    client = MassiveClient(api_key="test_secret")

    success_data = {
        "status": "OK",
        "results": [{"t": 1784102400000, "o": 100, "h": 101, "l": 99, "c": 100.5, "v": 1000}],
        "next_url": None,
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(success_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    http_429 = urllib.error.HTTPError(
        url="https://api.massive.com",
        code=429,
        msg="Too Many Requests",
        hdrs={"Retry-After": "0.01"},
        fp=io.BytesIO(b""),
    )

    with patch("urllib.request.urlopen", side_effect=[http_429, mock_resp]) as mock_open:
        with patch("time.sleep", return_value=None):
            results = client.fetch_custom_bars("MU", "2026-07-15", "2026-07-15")
            assert len(results) == 1
            assert mock_open.call_count == 2


def test_massive_client_401_credentials_error_mocked():
    client = MassiveClient(api_key="bad_key")
    http_401 = urllib.error.HTTPError(
        url="https://api.massive.com",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(b""),
    )

    with patch("urllib.request.urlopen", side_effect=http_401):
        with pytest.raises(MassiveCredentialsError):
            client.fetch_custom_bars("MU", "2026-07-15", "2026-07-15")


def test_ingest_massive_universe_end_to_end_mocked(tmp_path: Path):
    """End-to-end test of ingestion pipeline for all 7 symbols using mocked API returns."""
    t0_ms = int(datetime(2026, 7, 15, 13, 30, tzinfo=UTC).timestamp() * 1000)
    fake_bars = [
        {
            "t": t0_ms,
            "o": 100.0,
            "h": 105.0,
            "l": 95.0,
            "c": 102.0,
            "v": 50000.0,
            "vw": 101.0,
        },
        {
            "t": t0_ms + 60000,
            "o": 102.0,
            "h": 106.0,
            "l": 101.0,
            "c": 104.0,
            "v": 60000.0,
            "vw": 103.0,
        },
    ]

    with patch.object(MassiveClient, "fetch_custom_bars", return_value=fake_bars):
        success = ingest_massive_universe(
            start_date="2026-07-15",
            end_date="2026-07-15",
            data_dir=tmp_path,
            api_key="test_mock_key",
            reports_dir=tmp_path / "reports_manifests",
        )
        assert success is True

    # Check that all 7 CSV files exist
    symbols = ["MU", "SNDK", "SKHY", "AMD", "USD", "SMH", "SPY"]
    for sym in symbols:
        csv_file = tmp_path / f"{sym}.csv"
        assert csv_file.exists()
        assert len(csv_file.read_text(encoding="utf-8").strip().splitlines()) == 3

    # Check manifest
    manifest = load_dataset_manifest(tmp_path)
    assert manifest.data_status == "REAL_HISTORICAL_VERIFIED"
    assert manifest.is_verified_market_data is True
    assert manifest.provider == "Massive"
    assert manifest.bar_resolution == "1m"
    assert set(manifest.symbols) == set(symbols)
    assert "SKHY" in manifest.instrument_history_caveats

    # Verify that research gate accepts it with a 1m config
    cfg = EngineConfig()
    cfg.strategy.bar_interval = "1m"
    assert_research_dataset_verified(manifest, cfg)
