from datetime import UTC, datetime, timedelta

import pandas as pd

from tactical_engine.config import SignalConfig
from tactical_engine.data.models import Bar
from tactical_engine.signals.features import compute_bar_features
from tactical_engine.signals.pullback import generate_pullback_signals


def test_complete_feature_set():
    t0 = datetime(2026, 1, 5, 9, 30, tzinfo=UTC)
    bars = []
    price = 100.0
    for i in range(80):
        t = t0 + timedelta(minutes=i)
        price = price * (1.0 + (0.001 if i % 2 == 0 else -0.001))
        bars.append(
            Bar(
                symbol="MU",
                timestamp=t,
                open=price,
                high=price * 1.002,
                low=price * 0.998,
                close=price,
                volume=10000.0,
            )
        )

    df = compute_bar_features(bars, trend_window=30)
    assert len(df) == 80

    required_features = [
        "returns",
        "ret_5",
        "ret_15",
        "ret_60",
        "atr",
        "rolling_vol",
        "vwap_dist",
        "zscore",
        "trend_slope",
        "rel_volume",
        "dist_high",
        "dist_low",
        "time_of_day_minute",
        "is_event_blackout",
        "trend_ok",
    ]
    for feat in required_features:
        assert feat in df.columns, f"Missing feature: {feat}"


def test_relative_volume_filter_suppresses_low_volume_pullback():
    t0 = datetime(2026, 1, 5, 9, 30, tzinfo=UTC)
    # Row with pullback zscore but low relative volume
    df = pd.DataFrame(
        [
            {
                "symbol": "MU",
                "zscore": -2.0,
                "trend_ok": True,
                "rel_volume": 0.3,  # Below 0.7 threshold
                "is_event_blackout": False,
            }
        ],
        index=[t0],
    )

    cfg = SignalConfig(pullback_zscore=-1.5, relative_volume_filter=True)
    sigs = generate_pullback_signals(df, cfg)
    assert len(sigs) == 1
    assert sigs[0].action == "HOLD"  # Suppressed by relative volume

    # When relative volume filter is turned off, signal is emitted
    cfg_no_vol = SignalConfig(pullback_zscore=-1.5, relative_volume_filter=False)
    sigs2 = generate_pullback_signals(df, cfg_no_vol)
    assert sigs2[0].action == "ENTER_LONG"


def test_event_filter_suppresses_blackout_pullback():
    t0 = datetime(2026, 1, 5, 9, 30, tzinfo=UTC)
    df = pd.DataFrame(
        [
            {
                "symbol": "MU",
                "zscore": -2.0,
                "trend_ok": True,
                "rel_volume": 1.5,
                "is_event_blackout": True,  # Blackout active
            }
        ],
        index=[t0],
    )

    cfg = SignalConfig(pullback_zscore=-1.5, event_filter=True)
    sigs = generate_pullback_signals(df, cfg)
    assert len(sigs) == 1
    assert sigs[0].action == "HOLD"  # Suppressed by event blackout

    cfg_no_event = SignalConfig(pullback_zscore=-1.5, event_filter=False)
    sigs2 = generate_pullback_signals(df, cfg_no_event)
    assert sigs2[0].action == "ENTER_LONG"
