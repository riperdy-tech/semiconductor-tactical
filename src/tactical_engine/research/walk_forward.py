from datetime import datetime

from pydantic import BaseModel

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar
from tactical_engine.reports.metrics import PerformanceMetrics, calculate_metrics


class WalkForwardResult(BaseModel):
    train_metrics: PerformanceMetrics
    val_metrics: PerformanceMetrics
    test_metrics: PerformanceMetrics


def split_data_by_time(
    data: dict[str, list[Bar]],
    train_end: datetime,
    val_end: datetime,
) -> dict[str, dict[str, list[Bar]]]:
    train_split: dict[str, list[Bar]] = {}
    val_split: dict[str, list[Bar]] = {}
    test_split: dict[str, list[Bar]] = {}

    for sym, bars in data.items():
        train_split[sym] = [b for b in bars if b.timestamp <= train_end]
        val_split[sym] = [b for b in bars if train_end < b.timestamp <= val_end]
        test_split[sym] = [b for b in bars if b.timestamp > val_end]

    return {
        "train": train_split,
        "val": val_split,
        "test": test_split,
    }


def run_walk_forward(
    data: dict[str, list[Bar]],
    config: EngineConfig,
    train_ratio: float = 0.5,
    val_ratio: float = 0.25,
) -> WalkForwardResult:
    # Collect all timestamps
    all_timestamps = sorted(list(set(b.timestamp for bars in data.values() for b in bars)))
    n = len(all_timestamps)
    train_idx = int(n * train_ratio)
    val_idx = int(n * (train_ratio + val_ratio))

    train_end = all_timestamps[train_idx - 1]
    val_end = all_timestamps[val_idx - 1]

    splits = split_data_by_time(data, train_end, val_end)

    res_train = run_backtest(splits["train"], config)
    res_val = run_backtest(splits["val"], config)
    res_test = run_backtest(splits["test"], config)

    return WalkForwardResult(
        train_metrics=calculate_metrics(res_train),
        val_metrics=calculate_metrics(res_val),
        test_metrics=calculate_metrics(res_test),
    )
