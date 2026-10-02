from datetime import UTC, datetime, timedelta

from tactical_engine.backtest.state import TradeRecord
from tactical_engine.config import load_config
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.research.falsification import (
    run_strongest_day_exclusion_test,
    run_ticker_exclusion_test,
    stationary_block_bootstrap,
)


def test_stationary_block_bootstrap_shape_and_bounds() -> None:
    bars = generate_synthetic_bars("MU", num_bars=100, seed=42)
    res = stationary_block_bootstrap(
        bars=bars, expected_block_size=10, num_simulations=100, seed=42
    )

    assert res.ci_lower_pct <= res.median_return_pct <= res.ci_upper_pct
    assert 0.0 <= res.prob_positive <= 1.0
    assert len(res.simulated_returns) > 0


def test_ticker_exclusion_test() -> None:
    cfg = load_config("configs/base.yaml")
    data = {
        "MU": generate_synthetic_bars("MU", num_bars=100, seed=1),
        "AMD": generate_synthetic_bars("AMD", num_bars=100, seed=2),
    }

    res = run_ticker_exclusion_test(data=data, config=cfg)
    assert "MU" in res.results_by_excluded_ticker
    assert "AMD" in res.results_by_excluded_ticker
    assert isinstance(res.is_fragile_to_single_ticker, bool)


def test_strongest_day_exclusion_test() -> None:
    t1 = datetime(2026, 1, 5, 15, 0, tzinfo=UTC)
    t2 = datetime(2026, 1, 6, 15, 0, tzinfo=UTC)
    t3 = datetime(2026, 1, 7, 15, 0, tzinfo=UTC)

    trades = [
        TradeRecord(
            symbol="MU",
            side="buy",
            entry_time=t1 - timedelta(minutes=30),
            exit_time=t1,
            entry_price=100.0,
            exit_price=110.0,
            quantity=100,
            gross_pnl=1000.0,
            commissions=2.0,
            net_pnl=998.0,
            holding_period_minutes=30,
            exit_reason="take_profit",
        ),
        TradeRecord(
            symbol="MU",
            side="buy",
            entry_time=t2 - timedelta(minutes=30),
            exit_time=t2,
            entry_price=100.0,
            exit_price=105.0,
            quantity=100,
            gross_pnl=500.0,
            commissions=2.0,
            net_pnl=498.0,
            holding_period_minutes=30,
            exit_reason="take_profit",
        ),
        TradeRecord(
            symbol="MU",
            side="buy",
            entry_time=t3 - timedelta(minutes=30),
            exit_time=t3,
            entry_price=100.0,
            exit_price=98.0,
            quantity=100,
            gross_pnl=-200.0,
            commissions=2.0,
            net_pnl=-202.0,
            holding_period_minutes=30,
            exit_reason="stop_loss",
        ),
    ]

    res = run_strongest_day_exclusion_test(trades=trades)
    assert res.total_trading_days == 3
    assert res.baseline_net_pnl == 998.0 + 498.0 - 202.0
    assert len(res.top_day_dates) == 3
    # Top day is t1 with 998 net PnL
    assert res.top_day_pnls[0] == 998.0
    assert res.pnl_excluding_top_1 == round(498.0 - 202.0, 2)
    assert res.remains_positive_top_1 is True
    # Excluding top 3 leaves 0 or negative
    assert res.pnl_excluding_top_3 <= 0.0
