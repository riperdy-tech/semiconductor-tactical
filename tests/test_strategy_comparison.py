from datetime import UTC, datetime
from tactical_engine.config import EngineConfig
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.research.comparison import (
    StrategyComparisonResult,
    run_strategy_comparison,
)


def test_strategy_comparison_runner():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars(symbol="MU", num_bars=100, start_time=t0, seed=42)
    cfg = EngineConfig()

    result = run_strategy_comparison(data={"MU": bars}, base_config=cfg)

    assert isinstance(result, StrategyComparisonResult)
    assert result.literal_clone is not None
    assert result.risk_controlled is not None
    assert result.regime_adapted is not None
    assert len(result.cost_sensitivity) > 0
    assert len(result.leverage_sensitivity) > 0
