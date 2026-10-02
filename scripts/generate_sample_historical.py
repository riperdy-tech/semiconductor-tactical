"""Generates deterministic sample historical equity datasets for initial testing and CI."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd


def generate_realistic_ticker_csv(
    symbol: str,
    start_date: datetime,
    days: int,
    base_price: float,
    drift: float,
    vol: float,
    base_volume: float,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    price = base_price
    cur_date = start_date

    # Use deterministic pseudo-random sequence for repeatability
    seed = sum(ord(c) for c in symbol) + 12345
    import random

    rng = random.Random(seed)

    count = 0
    while count < days:
        # Skip weekends
        if cur_date.weekday() >= 5:
            cur_date += timedelta(days=1)
            continue

        ret = rng.gauss(drift, vol)
        close_p = max(0.5, price * (1.0 + ret))
        open_p = max(0.5, price * (1.0 + rng.gauss(0.0, vol * 0.4)))
        high_p = max(open_p, close_p) * (1.0 + abs(rng.gauss(0.005, vol * 0.5)))
        low_p = min(open_p, close_p) * (1.0 - abs(rng.gauss(0.005, vol * 0.5)))
        vol_noise = max(0.2, 1.0 + rng.gauss(0.0, 0.3))
        volume = int(base_volume * vol_noise)
        vwap = (open_p + high_p + low_p + close_p) / 4.0

        records.append(
            {
                "date": cur_date.strftime("%Y-%m-%d"),
                "open": round(open_p, 4),
                "high": round(high_p, 4),
                "low": round(low_p, 4),
                "close": round(close_p, 4),
                "volume": volume,
                "vwap": round(vwap, 4),
            }
        )

        price = close_p
        cur_date += timedelta(days=1)
        count += 1

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(
        f"Generated {output_path} with {len(df)} bars "
        f"({records[0]['date']} to {records[-1]['date']})"
    )


def main() -> None:
    # 2014-01-02 to 2015-12-31 (~500 trading days)
    start_dt = datetime(2014, 1, 2, tzinfo=UTC)
    trading_days = 250

    specs = {
        "MU": {"base_price": 22.0, "drift": 0.0004, "vol": 0.025, "volume": 20_000_000},
        "SNDK": {"base_price": 70.0, "drift": 0.0002, "vol": 0.022, "volume": 5_000_000},
        "SKHY": {"base_price": 35.0, "drift": 0.0003, "vol": 0.020, "volume": 3_000_000},
        "AMD": {"base_price": 3.8, "drift": -0.0002, "vol": 0.035, "volume": 15_000_000},
        "SMH": {"base_price": 45.0, "drift": 0.0005, "vol": 0.015, "volume": 4_000_000},
        "SPY": {"base_price": 185.0, "drift": 0.0004, "vol": 0.010, "volume": 80_000_000},
        "USD": {"base_price": 25.0, "drift": 0.0008, "vol": 0.030, "volume": 500_000},
    }

    target_dirs = [Path("data/processed"), Path("data/sample_historical")]
    for target_dir in target_dirs:
        for symbol, params in specs.items():
            csv_path = target_dir / f"{symbol}.csv"
            generate_realistic_ticker_csv(
                symbol=symbol,
                start_date=start_dt,
                days=trading_days,
                base_price=params["base_price"],
                drift=params["drift"],
                vol=params["vol"],
                base_volume=params["volume"],
                output_path=csv_path,
            )


if __name__ == "__main__":
    main()
