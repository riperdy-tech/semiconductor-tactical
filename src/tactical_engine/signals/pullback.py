import pandas as pd

from tactical_engine.config import SignalConfig
from tactical_engine.data.models import SignalIntent


def generate_pullback_signals(df: pd.DataFrame, config: SignalConfig) -> list[SignalIntent]:
    signals = []
    if df.empty:
        return signals

    symbol = str(df["symbol"].iloc[0])
    for timestamp, row in df.iterrows():
        # 1. Pullback condition: zscore <= configured threshold
        is_pullback = row["zscore"] <= config.pullback_zscore

        # 2. Trend filter
        trend_intact = row["trend_ok"] if config.sector_filter else True

        # 3. Relative volume filter: check volume participation
        rel_vol_ok = True
        if config.relative_volume_filter and "rel_volume" in row:
            rel_vol_ok = row["rel_volume"] >= 0.7

        # 4. Event blackout filter
        event_ok = True
        if config.event_filter and "is_event_blackout" in row:
            event_ok = not bool(row["is_event_blackout"])

        if is_pullback and trend_intact and rel_vol_ok and event_ok:
            signals.append(
                SignalIntent(
                    symbol=symbol,
                    timestamp=timestamp,  # type: ignore
                    action="ENTER_LONG",
                    strength=abs(float(row["zscore"])),
                    reason=(
                        f"pullback_z={row['zscore']:.2f}:rel_vol={row.get('rel_volume', 1.0):.2f}"
                    ),
                )
            )
        else:
            signals.append(
                SignalIntent(
                    symbol=symbol,
                    timestamp=timestamp,  # type: ignore
                    action="HOLD",
                )
            )
    return signals
