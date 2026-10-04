from datetime import UTC, datetime
from pathlib import Path

import pytest

from tactical_engine.data.historical import (
    CsvEquityDataProvider,
    HistoricalDataMissingError,
    load_historical_universe,
)
from tactical_engine.data.models import Bar
from tactical_engine.data.validation import (
    detect_duplicates,
    detect_time_gaps,
    validate_bar_sequence,
    validate_symbol_bars,
)


def test_csv_provider_loads_and_hashes(tmp_path: Path):
    csv_file = tmp_path / "TEST.csv"
    csv_content = (
        "date,open,high,low,close,volume,vwap\n"
        "2024-01-02,100.0,105.0,99.0,104.0,1000000,102.5\n"
        "2024-01-03,104.0,108.0,103.0,107.0,1200000,106.0\n"
        "2024-01-04,107.0,107.5,102.0,103.0,900000,104.2\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    provider = CsvEquityDataProvider(data_dir=tmp_path, adjustment_status="split_adjusted")
    bars = provider.load_bars("TEST")

    assert len(bars) == 3
    assert bars[0].symbol == "TEST"
    assert bars[0].close == 104.0
    assert bars[0].provider == "csv"
    assert bars[0].adjustment_status == "split_adjusted"
    assert bars[0].timestamp < bars[1].timestamp < bars[2].timestamp

    prov = provider.get_provenance("TEST")
    assert prov.symbol == "TEST"
    assert prov.row_count == 3
    assert len(prov.file_sha256) == 64
    assert prov.start_time == bars[0].timestamp
    assert prov.end_time == bars[-1].timestamp


def test_csv_provider_missing_symbol_raises(tmp_path: Path):
    provider = CsvEquityDataProvider(data_dir=tmp_path)
    with pytest.raises(HistoricalDataMissingError):
        provider.load_bars("NONEXISTENT")


def test_validation_detects_duplicates_and_monotonicity():
    t1 = datetime(2024, 1, 2, 9, 30, tzinfo=UTC)
    t2 = datetime(2024, 1, 2, 9, 31, tzinfo=UTC)

    b1 = Bar(symbol="TEST", timestamp=t1, open=10, high=12, low=9, close=11)
    b2 = Bar(symbol="TEST", timestamp=t1, open=11, high=13, low=10, close=12)
    b3 = Bar(symbol="TEST", timestamp=t2, open=12, high=14, low=11, close=13)

    dupes = detect_duplicates([b1, b2, b3])
    assert len(dupes) == 1
    assert dupes[0] == t1

    with pytest.raises(ValueError, match="Monotonic timestamp violation"):
        validate_bar_sequence([b1, b2, b3])


def test_validation_detects_ohlc_and_gaps():
    t1 = datetime(2024, 1, 2, tzinfo=UTC)
    t2 = datetime(2024, 1, 15, tzinfo=UTC)  # 13 day gap

    b1 = Bar(symbol="TEST", timestamp=t1, open=100, high=105, low=98, close=102, volume=1000)
    b2 = Bar(symbol="TEST", timestamp=t2, open=102, high=106, low=101, close=105, volume=1000)

    gaps = detect_time_gaps([b1, b2], max_gap_seconds=86400 * 5)
    assert len(gaps) == 1
    assert gaps[0] == (t1, t2)

    val_res = validate_symbol_bars("TEST", [b1, b2], max_gap_seconds=86400 * 5)
    assert val_res.is_valid is True  # gaps are warnings, not fatal errors
    assert len(val_res.warnings) >= 1
    assert val_res.gaps_count == 1


def test_load_historical_universe_success_and_digest(tmp_path: Path):
    for sym in ["MU", "AMD"]:
        content = (
            "date,open,high,low,close,volume\n"
            "2024-01-02,50.0,52.0,49.0,51.0,100000\n"
            "2024-01-03,51.0,53.0,50.0,52.0,120000\n"
        )
        (tmp_path / f"{sym}.csv").write_text(content, encoding="utf-8")

    ds = load_historical_universe(data_dir=tmp_path, symbols=["MU", "AMD"])
    assert len(ds.bars_by_symbol) == 2
    assert "MU" in ds.bars_by_symbol
    assert "AMD" in ds.bars_by_symbol
    assert len(ds.aggregate_data_hash) == 64
    assert len(ds.provenance_by_symbol) == 2


def test_load_historical_universe_missing_symbol_fails(tmp_path: Path):
    (tmp_path / "MU.csv").write_text(
        "date,open,high,low,close,volume\n2024-01-02,50,52,49,51,1000\n",
        encoding="utf-8",
    )
    with pytest.raises(HistoricalDataMissingError, match="AMD"):
        load_historical_universe(data_dir=tmp_path, symbols=["MU", "AMD"])


def test_cadence_mismatch_detected_for_1m_when_daily_provided(tmp_path: Path):
    content = (
        "date,open,high,low,close,volume\n"
        "2024-01-02,50.0,52.0,49.0,51.0,100000\n"
        "2024-01-03,51.0,53.0,50.0,52.0,120000\n"
    )
    (tmp_path / "MU.csv").write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="Resolution cadence mismatch"):
        load_historical_universe(data_dir=tmp_path, symbols=["MU"], resolution="1m")


def test_cadence_mismatch_detected_for_1d_when_intraday_provided():
    t1 = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    t2 = datetime(2024, 1, 2, 14, 31, tzinfo=UTC)  # 60s
    b1 = Bar(symbol="TEST", timestamp=t1, open=10, high=11, low=9, close=10.5)
    b2 = Bar(symbol="TEST", timestamp=t2, open=10.5, high=11.2, low=10.1, close=10.8)

    val = validate_symbol_bars("TEST", [b1, b2], expected_interval="1d")
    assert val.is_valid is False
    assert any("Resolution cadence mismatch" in e for e in val.errors)
