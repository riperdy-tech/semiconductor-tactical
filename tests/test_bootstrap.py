from datetime import UTC, datetime
from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.research.bootstrap import (
    bootstrap_trade_returns,
    run_random_entry_control,
)


def test_bootstrap_trade_returns():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars(symbol="MU", num_bars=150, start_time=t0, seed=42)
    cfg = EngineConfig()
    result = run_backtest(data={"MU": bars}, config=cfg)

    dist = bootstrap_trade_returns(trades=result.trades, num_simulations=100, seed=42)
    assert dist.num_simulations == 100
    assert len(dist.mean_returns) == 100
    assert dist.ci_lower <= dist.ci_upper


def test_random_entry_control():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars(symbol="MU", num_bars=100, start_time=t0, seed=42)
    cfg = EngineConfig()
    control_result = run_random_entry_control(
        data={"MU": bars},
        config=cfg,
        target_trades=3,
        seed=42,
    )
    assert control_result.total_trades >= 0
    assert control_result.final_equity > 0
