from datetime import datetime, timedelta, timezone
import numpy as np
from tactical_engine.data.models import Bar


def generate_synthetic_bars(
    symbol: str,
    num_bars: int = 200,
    base_price: float = 100.0,
    seed: int = 42,
    start_time: datetime | None = None,
    interval_minutes: int = 1,
) -> list[Bar]:
    rng = np.random.default_rng(seed)
    if start_time is None:
        start_time = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)

    # Random walk with slight drift and occasional pullbacks
    returns = rng.normal(loc=0.0001, scale=0.002, size=num_bars)
    # Inject deliberate pullback at bar 30 and 80
    if num_bars > 35:
        returns[30:33] = -0.015
    if num_bars > 85:
        returns[80:83] = -0.018

    prices = base_price * np.exp(np.cumsum(returns))
    bars = []
    current_time = start_time

    for i in range(num_bars):
        close_p = float(prices[i])
        open_p = float(prices[i - 1]) if i > 0 else base_price
        high_p = max(open_p, close_p) + abs(float(rng.normal(0, 0.2)))
        low_p = min(open_p, close_p) - abs(float(rng.normal(0, 0.2)))
        vol = float(rng.uniform(5000, 25000))
        vwap_p = (open_p + high_p + low_p + close_p) / 4.0

        bars.append(
            Bar(
                symbol=symbol,
                timestamp=current_time,
                open=round(open_p, 4),
                high=round(high_p, 4),
                low=round(low_p, 4),
                close=round(close_p, 4),
                volume=round(vol, 1),
                vwap=round(vwap_p, 4),
            )
        )
        current_time += timedelta(minutes=interval_minutes)

    return bars
