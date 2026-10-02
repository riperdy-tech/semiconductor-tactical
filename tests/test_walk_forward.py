from datetime import UTC, datetime
from tactical_engine.config import EngineConfig
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.research.walk_forward import run_walk_forward, split_data_by_time


def test_split_data_by_time():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars(symbol="MU", num_bars=100, start_time=t0, seed=42)
    # Split: train first 40, val next 30, test remaining 30
    t_train_end = bars[39].timestamp
    t_val_end = bars[69].timestamp

    splits = split_data_by_time(
        data={"MU": bars},
        train_end=t_train_end,
        val_end=t_val_end,
    )

    assert "train" in splits
    assert "val" in splits
    assert "test" in splits
    assert len(splits["train"]["MU"]) == 40
    assert len(splits["val"]["MU"]) == 30
    assert len(splits["test"]["MU"]) == 30


def test_run_walk_forward_evaluation():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars(symbol="MU", num_bars=120, start_time=t0, seed=42)
    cfg = EngineConfig()
    result = run_walk_forward(
        data={"MU": bars},
        config=cfg,
        train_ratio=0.5,
        val_ratio=0.25,
    )
    assert result.train_metrics is not None
    assert result.val_metrics is not None
    assert result.test_metrics is not None
