from tactical_engine.data.models import Bar


def validate_bar_sequence(bars: list[Bar]) -> None:
    if not bars:
        return
    for i in range(1, len(bars)):
        if bars[i].timestamp <= bars[i - 1].timestamp:
            raise ValueError(
                f"Monotonic timestamp violation: {bars[i].timestamp} <= {bars[i - 1].timestamp}"
            )
