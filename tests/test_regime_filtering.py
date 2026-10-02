from datetime import UTC, datetime, timedelta

from tactical_engine.data.models import Bar
from tactical_engine.signals.regime import (
    BenchmarkRegimeProvider,
    ExternalRegimeProvider,
)


def make_test_bars(symbol: str, trend: str, count: int = 50) -> list[Bar]:
    t0 = datetime(2026, 1, 5, 9, 30, tzinfo=UTC)
    bars = []
    price = 100.0
    drift = 0.01 if trend == "up" else -0.01
    for i in range(count):
        t = t0 + timedelta(minutes=i)
        price *= 1.0 + drift
        bars.append(
            Bar(
                symbol=symbol,
                timestamp=t,
                open=price,
                high=price * 1.002,
                low=price * 0.998,
                close=price,
                volume=10000.0,
            )
        )
    return bars


def test_benchmark_regime_provider_sector_filter():
    # SMH in downtrend, SPY in uptrend
    smh_down = make_test_bars("SMH", trend="down", count=50)
    spy_up = make_test_bars("SPY", trend="up", count=50)

    # When filter_mode is "sector": SMH downtrend should block trades
    provider_sector = BenchmarkRegimeProvider(
        sector_bars=smh_down,
        broad_bars=spy_up,
        trend_window=20,
        filter_mode="sector",
    )
    last_ts = smh_down[-1].timestamp
    state_sector = provider_sector.get_regime_state(last_ts)
    assert state_sector.sector_trend_ok is False
    assert state_sector.broad_trend_ok is True
    assert state_sector.regime_allows_trade is False

    # When filter_mode is "broad": SPY uptrend should allow trades
    provider_broad = BenchmarkRegimeProvider(
        sector_bars=smh_down,
        broad_bars=spy_up,
        trend_window=20,
        filter_mode="broad",
    )
    state_broad = provider_broad.get_regime_state(last_ts)
    assert state_broad.regime_allows_trade is True

    # When filter_mode is "none": always allows trades
    provider_none = BenchmarkRegimeProvider(
        sector_bars=smh_down,
        broad_bars=spy_up,
        trend_window=20,
        filter_mode="none",
    )
    state_none = provider_none.get_regime_state(last_ts)
    assert state_none.regime_allows_trade is True


def test_external_regime_provider_csv(tmp_path):
    t0 = datetime(2026, 1, 5, 9, 30, tzinfo=UTC)
    csv_file = tmp_path / "regime.csv"
    csv_file.write_text(
        f"timestamp,regime_allows_trade,volatility_regime\n{t0.isoformat()},false,HIGH\n",
        encoding="utf-8",
    )

    provider = ExternalRegimeProvider(csv_file)
    state = provider.get_regime_state(t0)
    assert state.regime_allows_trade is False
    assert state.volatility_regime == "HIGH"
