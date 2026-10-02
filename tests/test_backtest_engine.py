from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.synthetic import generate_synthetic_bars


def test_deterministic_backtest_run():
    bars_mu = generate_synthetic_bars(symbol="MU", num_bars=120, seed=42)
    cfg = EngineConfig()
    result1 = run_backtest(data={"MU": bars_mu}, config=cfg)
    result2 = run_backtest(data={"MU": bars_mu}, config=cfg)

    assert result1.total_trades == result2.total_trades
    assert result1.equity_curve == result2.equity_curve
    assert len(result1.trades) >= 0
    assert result1.final_equity > 0
