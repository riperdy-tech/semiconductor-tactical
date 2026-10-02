import pandas as pd

from tactical_engine.config import SignalConfig
from tactical_engine.data.models import SignalIntent


def generate_pullback_signals(df: pd.DataFrame, config: SignalConfig) -> list[SignalIntent]:
    signals = []
    if df.empty:
        return signals

    symbol = str(df["symbol"].iloc[0])
    for timestamp, row in df.iterrows():
        # Hypothesis: buy when zscore < threshold AND trend_ok is True
        is_pullback = row["zscore"] <= config.pullback_zscore
        trend_intact = row["trend_ok"] if config.sector_filter else True

        if is_pullback and trend_intact:
            signals.append(
                SignalIntent(
                    symbol=symbol,
                    timestamp=timestamp,  # type: ignore
                    action="ENTER_LONG",
                    strength=abs(float(row["zscore"])),
                    reason=f"pullback_zscore={row['zscore']:.2f}",
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
