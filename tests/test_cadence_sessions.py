from datetime import UTC, datetime, timedelta

from tactical_engine.data.models import Bar
from tactical_engine.data.validation import validate_resolution_cadence, validate_symbol_bars


def test_valid_1m_session_data_passes():
    # Regular 1-minute bars across 2 trading sessions
    bars = []
    # Day 1: 09:30 to 10:00 (30 bars)
    t1 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    for i in range(30):
        bars.append(
            Bar(
                symbol="MU",
                timestamp=t1 + timedelta(minutes=i),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000,
            )
        )

    # Overnight gap to Day 2: 09:30 to 10:00 (30 bars)
    t2 = datetime(2026, 1, 6, 14, 30, tzinfo=UTC)
    for i in range(30):
        bars.append(
            Bar(
                symbol="MU",
                timestamp=t2 + timedelta(minutes=i),
                open=101.0,
                high=102.0,
                low=100.0,
                close=101.5,
                volume=1000,
            )
        )

    is_valid, msg = validate_resolution_cadence(bars, declared_interval="1m")
    assert is_valid is True
    assert msg == ""


def test_large_legitimate_overnight_weekend_gaps_do_not_falsely_reject():
    # 1-minute bars with Friday afternoon session, 65.5-hour weekend gap, and Monday morning session
    bars = []
    # Friday 15:30 to 16:00
    fri = datetime(2026, 1, 9, 20, 30, tzinfo=UTC)
    for i in range(30):
        bars.append(
            Bar(
                symbol="MU",
                timestamp=fri + timedelta(minutes=i),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000,
            )
        )

    # Monday 09:30 to 10:00 (weekend gap of over 65 hours)
    mon = datetime(2026, 1, 12, 14, 30, tzinfo=UTC)
    for i in range(30):
        bars.append(
            Bar(
                symbol="MU",
                timestamp=mon + timedelta(minutes=i),
                open=102.0,
                high=103.0,
                low=101.0,
                close=102.5,
                volume=1000,
            )
        )

    is_valid, msg = validate_resolution_cadence(bars, declared_interval="1m")
    assert is_valid is True
    assert msg == ""


def test_valid_daily_data_with_weekend_and_holiday_gaps_passes():
    # Daily bars including weekend (3 days) and holiday (4 days) gaps
    dates = [
        datetime(2026, 1, 5, 21, 0, tzinfo=UTC),  # Monday
        datetime(2026, 1, 6, 21, 0, tzinfo=UTC),  # Tuesday
        datetime(2026, 1, 7, 21, 0, tzinfo=UTC),  # Wednesday
        datetime(2026, 1, 8, 21, 0, tzinfo=UTC),  # Thursday
        datetime(2026, 1, 9, 21, 0, tzinfo=UTC),  # Friday
        datetime(2026, 1, 12, 21, 0, tzinfo=UTC),  # Monday (weekend gap)
        datetime(2026, 1, 20, 21, 0, tzinfo=UTC),  # Tuesday (MLK holiday gap)
    ]
    bars = [
        Bar(symbol="MU", timestamp=d, open=50, high=52, low=49, close=51, volume=10000)
        for d in dates
    ]

    is_valid, msg = validate_resolution_cadence(bars, declared_interval="1d")
    assert is_valid is True
    assert msg == ""


def test_daily_data_under_1m_config_is_rejected():
    dates = [
        datetime(2026, 1, 5, 21, 0, tzinfo=UTC),
        datetime(2026, 1, 6, 21, 0, tzinfo=UTC),
        datetime(2026, 1, 7, 21, 0, tzinfo=UTC),
    ]
    bars = [
        Bar(symbol="MU", timestamp=d, open=50, high=52, low=49, close=51, volume=10000)
        for d in dates
    ]

    val = validate_symbol_bars("MU", bars, expected_interval="1m")
    assert val.is_valid is False
    assert any("Resolution cadence mismatch" in err for err in val.errors)
    assert any("daily" in err.lower() for err in val.errors)


def test_intraday_data_under_1d_config_is_rejected():
    # Intraday 1-minute bars submitted under daily config
    t1 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = [
        Bar(
            symbol="MU",
            timestamp=t1 + timedelta(minutes=i),
            open=100,
            high=101,
            low=99,
            close=100.5,
            volume=5000,
        )
        for i in range(10)
    ]

    val = validate_symbol_bars("MU", bars, expected_interval="1d")
    assert val.is_valid is False
    assert any("Resolution cadence mismatch" in err for err in val.errors)
    assert any("intraday" in err.lower() for err in val.errors)
