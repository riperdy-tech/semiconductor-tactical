from datetime import UTC, datetime

import pandas as pd

from tactical_engine.config import SignalConfig
from tactical_engine.signals.directional_fidelity import (
    check_pullback_predicate,
    check_strength_predicate,
    check_trend_predicate,
    generate_directional_fidelity_signals,
)


def test_trend_predicate():
    # Bullish trend row
    row_bull = pd.Series({"trend_ok": True, "trend_slope": 0.02})
    ok, msg = check_trend_predicate(row_bull, sector_filter=False)
    assert ok
    assert msg == "trend_intact"

    # Bearish slope
    row_bear_slope = pd.Series({"trend_ok": True, "trend_slope": -0.01})
    ok, _ = check_trend_predicate(row_bear_slope, sector_filter=False)
    assert not ok

    # Bearish MA alignment
    row_bear_ma = pd.Series({"trend_ok": False, "trend_slope": 0.02})
    ok, _ = check_trend_predicate(row_bear_ma, sector_filter=False)
    assert not ok


def test_pullback_predicate():
    # Valid pullback: 1.5% dip from high, closing in upper half of bar
    row_valid = pd.Series(
        {
            "dist_high": -0.015,
            "high": 100.0,
            "low": 98.0,
            "close": 99.2,  # (99.2 - 98) / 2 = 0.60 > 0.35 threshold
            "returns": 0.001,
        }
    )
    ok, msg = check_pullback_predicate(row_valid, 0.005, 0.030, 0.35)
    assert ok
    assert "pullback_confirmed" in msg

    # Too shallow dip (< 0.5%)
    row_shallow = pd.Series(
        {
            "dist_high": -0.002,
            "high": 100.0,
            "low": 99.5,
            "close": 99.8,
            "returns": 0.001,
        }
    )
    ok, _ = check_pullback_predicate(row_shallow, 0.005, 0.030, 0.35)
    assert not ok

    # Too deep dip (> 3.0% falling knife)
    row_deep = pd.Series(
        {
            "dist_high": -0.045,
            "high": 100.0,
            "low": 95.0,
            "close": 95.5,
            "returns": -0.02,
        }
    )
    ok, _ = check_pullback_predicate(row_deep, 0.005, 0.030, 0.35)
    assert not ok

    # Dip within range but unstabilized (closing at dead low, negative return)
    row_unstabilized = pd.Series(
        {
            "dist_high": -0.020,
            "high": 100.0,
            "low": 98.0,
            "close": 98.05,  # (98.05 - 98) / 2 = 0.025 < 0.35
            "returns": -0.008,
        }
    )
    ok, msg = check_pullback_predicate(row_unstabilized, 0.005, 0.030, 0.35)
    assert not ok
    assert msg == "pullback_not_stabilized"


def test_strength_predicate():
    # At high with positive return
    row_str = pd.Series({"dist_high": -0.001, "returns": 0.005, "trend_ok": True})
    assert check_strength_predicate(row_str)

    # Pulled back
    row_weak = pd.Series({"dist_high": -0.020, "returns": 0.005, "trend_ok": True})
    assert not check_strength_predicate(row_weak)


def test_generate_directional_fidelity_signals():
    ts = datetime(2026, 7, 10, 14, 0, tzinfo=UTC)
    df = pd.DataFrame(
        [
            {
                "symbol": "MU",
                "open": 98.5,
                "high": 100.0,
                "low": 98.0,
                "close": 99.0,
                "volume": 10000.0,
                "rel_volume": 1.2,
                "trend_ok": True,
                "trend_slope": 0.015,
                "dist_high": -0.010,
                "returns": 0.002,
                "atr": 0.50,
                "is_event_blackout": False,
            }
        ],
        index=[ts],
    )

    cfg = SignalConfig(
        signal_family="directional_fidelity",
        sector_filter=False,
        relative_volume_filter=True,
        pullback_min_pct=0.005,
        pullback_max_pct=0.030,
        swing_target_atr=2.5,
        swing_stop_atr=1.5,
    )

    signals = generate_directional_fidelity_signals(df, cfg)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.action == "ENTER_LONG"
    assert sig.symbol == "MU"
    assert sig.stop_price == 99.0
    assert sig.target_price == round(99.0 + 2.5 * 0.50, 4)
    assert "fidelity_swing" in sig.reason
