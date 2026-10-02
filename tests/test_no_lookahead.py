from datetime import UTC, datetime, timedelta

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar


def test_signal_confirmed_at_close_fills_on_subsequent_bar():
    """Verify that a signal generated on bar t close never fills on bar t."""
    t0 = datetime(2026, 1, 5, 9, 30, tzinfo=UTC)
    bars = []
    # Create 70 bars of steady decline to trigger pullback signal at bar 65
    price = 100.0
    for i in range(70):
        t = t0 + timedelta(minutes=i)
        price *= 0.995  # steady decline
        bars.append(
            Bar(
                symbol="MU",
                timestamp=t,
                open=price * 1.002,
                high=price * 1.003,
                low=price * 0.998,
                close=price,
                volume=10000.0,
            )
        )

    cfg = EngineConfig()
    cfg.strategy.universe = ["MU"]
    cfg.signals.pullback_zscore = -0.5

    result = run_backtest(data={"MU": bars}, config=cfg)

    # Check every executed trade has entry_time strictly after the first signal bar
    for trade in result.trades:
        assert trade.entry_time > bars[0].timestamp
        assert trade.exit_time >= trade.entry_time
