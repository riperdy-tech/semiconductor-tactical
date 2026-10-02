from datetime import datetime, timedelta, timezone
from tactical_engine.config import ExitConfig
from tactical_engine.data.models import Bar
from tactical_engine.signals.exits import check_exit_condition


def test_atr_exit_stop_hit():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    cfg = ExitConfig(family="atr", stop_atr=1.0, target_atr=1.5)
    # Entry at 100 with ATR = 2.0 -> stop at 98.0
    bar = Bar(symbol="MU", timestamp=t0, open=99.0, high=99.5, low=97.5, close=98.0, volume=100)
    should_exit, reason = check_exit_condition(
        entry_price=100.0,
        entry_time=t0,
        current_bar=bar,
        atr=2.0,
        config=cfg,
    )
    assert should_exit is True
    assert "stop" in reason


def test_time_exit():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    t1 = t0 + timedelta(minutes=130)
    cfg = ExitConfig(family="time", max_hold_minutes=120)
    bar = Bar(symbol="MU", timestamp=t1, open=100, high=101, low=99, close=100, volume=100)
    should_exit, reason = check_exit_condition(
        entry_price=100.0,
        entry_time=t0,
        current_bar=bar,
        atr=2.0,
        config=cfg,
    )
    assert should_exit is True
    assert "time_stop" in reason
