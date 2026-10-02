import numpy as np
import pandas as pd

from tactical_engine.data.models import Bar


def compute_bar_features(bars: list[Bar], trend_window: int = 60) -> pd.DataFrame:
    """Compute complete feature set for tactical signals.

    Features:
    - returns (1, 5, 15, 60 bar horizon returns)
    - ATR (14-period) and rolling volatility
    - VWAP distance
    - pullback / displacement z-score
    - trend slope over trend_window
    - relative volume (vs 20-period rolling mean)
    - distance from recent 20-bar high/low
    - time of day in minutes
    - event blackout status
    - trend_ok filter
    """
    if not bars:
        return pd.DataFrame()

    data = [
        {
            "timestamp": b.timestamp,
            "symbol": b.symbol,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
            "vwap": b.vwap or b.close,
        }
        for b in bars
    ]
    df = pd.DataFrame(data).set_index("timestamp").sort_index()

    # Multi-horizon returns
    df["returns"] = np.log(df["close"] / df["close"].shift(1)).fillna(0.0)
    df["ret_5"] = df["close"].pct_change(periods=5).fillna(0.0)
    df["ret_15"] = df["close"].pct_change(periods=15).fillna(0.0)
    df["ret_60"] = df["close"].pct_change(periods=60).fillna(0.0)

    # True Range & ATR
    prev_close = df["close"].shift(1).fillna(df["open"])
    tr = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            np.abs(df["high"] - prev_close),
            np.abs(df["low"] - prev_close),
        ),
    )
    df["atr"] = tr.rolling(window=14, min_periods=1).mean()
    df["rolling_vol"] = df["returns"].rolling(window=20, min_periods=5).std().fillna(0.0)

    # Rolling mean & std for displacement z-score (pullback hypothesis)
    rolling_mean = df["close"].rolling(window=trend_window, min_periods=10).mean()
    rolling_std = df["close"].rolling(window=trend_window, min_periods=10).std().replace(0, np.nan)
    df["zscore"] = ((df["close"] - rolling_mean) / rolling_std).fillna(0.0)

    # VWAP distance
    df["vwap_dist"] = (df["close"] - df["vwap"]) / df["vwap"]

    # Trend slope: percentage change over half of trend window
    half_w = max(2, trend_window // 2)
    df["trend_slope"] = (
        (df["close"] - df["close"].shift(half_w)) / df["close"].shift(half_w)
    ).fillna(0.0)

    # Relative volume: current volume / 20-period rolling average volume
    rolling_vol_mean = df["volume"].rolling(window=20, min_periods=1).mean().replace(0, np.nan)
    df["rel_volume"] = (df["volume"] / rolling_vol_mean).fillna(1.0)

    # Distance from recent 20-period high/low
    recent_high = df["high"].rolling(window=20, min_periods=1).max()
    recent_low = df["low"].rolling(window=20, min_periods=1).min()
    df["dist_high"] = ((df["close"] - recent_high) / recent_high).fillna(0.0)
    df["dist_low"] = ((df["close"] - recent_low) / recent_low).fillna(0.0)

    # Time of day (minutes from midnight UTC)
    df["time_of_day_minute"] = [ts.hour * 60 + ts.minute for ts in df.index]

    # Event blackout status (default False unless external event provider sets it)
    df["is_event_blackout"] = False

    # Trend filter: fast moving average >= slow moving average
    fast_ma = df["close"].rolling(window=max(5, trend_window // 4), min_periods=1).mean()
    slow_ma = df["close"].rolling(window=trend_window, min_periods=1).mean()
    df["trend_ok"] = fast_ma >= slow_ma

    return df
