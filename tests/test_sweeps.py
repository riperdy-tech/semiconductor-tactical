from datetime import UTC, datetime
from tactical_engine.config import EngineConfig
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.research.sweeps import ParameterGrid, run_parameter_sweep


def test_parameter_sweep_execution():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars(symbol="MU", num_bars=100, start_time=t0, seed=42)
    cfg = EngineConfig()

    grid = ParameterGrid(
        pullback_zscores=[-1.0, -1.5],
        target_atrs=[1.0],
        stop_atrs=[1.0],
        max_hold_minutes=[60],
    )

    results = run_parameter_sweep(data={"MU": bars}, base_config=cfg, grid=grid)
    assert len(results) == 2
    assert results[0].params["pullback_zscore"] == -1.0
    assert results[1].params["pullback_zscore"] == -1.5
    assert results[0].metrics is not None
