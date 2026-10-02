import numpy as np
import pandas as pd

from tactical_engine.data.models import Bar


def compute_bar_features(bars: list[Bar], trend_window: int = 60) -> pd.DataFrame:
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

    # Log returns
    df["returns"] = np.log(df["close"] / df["close"].shift(1)).fillna(0.0)

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

    # Rolling mean & std for displacement z-score (pullback hypothesis)
    rolling_mean = df["close"].rolling(window=trend_window, min_periods=10).mean()
    rolling_std = df["close"].rolling(window=trend_window, min_periods=10).std().replace(0, np.nan)
    df["zscore"] = ((df["close"] - rolling_mean) / rolling_std).fillna(0.0)

    # VWAP distance
    df["vwap_dist"] = (df["close"] - df["vwap"]) / df["vwap"]

    # Trend filter: fast moving average > slow moving average or price above rolling mean
    fast_ma = df["close"].rolling(window=max(5, trend_window // 4), min_periods=1).mean()
    slow_ma = df["close"].rolling(window=trend_window, min_periods=1).mean()
    df["trend_ok"] = fast_ma >= slow_ma

    return df
