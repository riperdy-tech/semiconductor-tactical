from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType, SignalIntent
from tactical_engine.data.validation import validate_bar_sequence


def test_bar_validation_success():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    bar = Bar(
        symbol="MU",
        timestamp=t0,
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.5,
        volume=10000.0,
        vwap=101.0,
    )
    assert bar.high >= bar.low
    assert bar.volume >= 0.0


def test_bar_validation_invalid_high_low():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        Bar(
            symbol="MU",
            timestamp=t0,
            open=100.0,
            high=95.0,  # high < low is invalid
            low=99.0,
            close=97.0,
            volume=100.0,
        )


def test_validate_bar_sequence_order():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=timezone.utc)
    b1 = Bar(symbol="MU", timestamp=t1, open=10, high=11, low=9, close=10, volume=10)
    b0 = Bar(symbol="MU", timestamp=t0, open=10, high=11, low=9, close=10, volume=10)
    with pytest.raises(ValueError, match="Monotonic"):
        validate_bar_sequence([b1, b0])  # Non-monotonic
