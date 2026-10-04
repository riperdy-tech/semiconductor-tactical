from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import BaseModel

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig, ResearchConfig
from tactical_engine.data.models import Bar
from tactical_engine.reports.metrics import PerformanceMetrics, calculate_metrics


class WalkForwardResult(BaseModel):
    train_metrics: PerformanceMetrics
    val_metrics: PerformanceMetrics
    test_metrics: PerformanceMetrics


@dataclass
class TrainValTestSplitResult:
    is_available: bool
    status_reason: str
    train: dict[str, list[Bar]]
    validation: dict[str, list[Bar]]
    test: dict[str, list[Bar]]
    train_range: tuple[datetime | None, datetime | None] = (None, None)
    validation_range: tuple[datetime | None, datetime | None] = (None, None)
    test_range: tuple[datetime | None, datetime | None] = (None, None)


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


def split_data_train_val_test(
    data: dict[str, list[Bar]],
    research_config: ResearchConfig,
) -> TrainValTestSplitResult:
    """Explicitly split data into disjoint train, validation, and test datasets.

    Requires explicit 'train_end', 'validation_end', and 'test_start'.
    Guarantees no timestamp appears in more than one partition.
    Test partition begins at or after test_start.
    """
    if not (
        research_config.train_end and research_config.validation_end and research_config.test_start
    ):
        return TrainValTestSplitResult(
            is_available=False,
            status_reason=(
                "OOS train/validation/test evaluation unavailable: "
                "research_config requires explicit 'train_end', 'validation_end', "
                "and 'test_start' date boundaries."
            ),
            train={},
            validation={},
            test={},
        )

    def _parse(dt_str: str) -> datetime:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt

    train_end = _parse(research_config.train_end)
    val_end = _parse(research_config.validation_end)
    test_start = _parse(research_config.test_start)

    start_dt = _parse(research_config.start) if research_config.start else None
    end_dt = _parse(research_config.end) if research_config.end else None

    if not (train_end <= val_end <= test_start):
        return TrainValTestSplitResult(
            is_available=False,
            status_reason=(
                f"Invalid date boundary ordering: train_end ({train_end}) <= "
                f"validation_end ({val_end}) <= test_start ({test_start}) violated."
            ),
            train={},
            validation={},
            test={},
        )

    train_split: dict[str, list[Bar]] = {}
    val_split: dict[str, list[Bar]] = {}
    test_split: dict[str, list[Bar]] = {}

    for sym, bars in data.items():
        # Mutually disjoint partitions:
        # train: start_dt <= ts < train_end
        # validation: train_end <= ts < test_start (and ts <= val_end)
        # test: test_start <= ts <= end_dt
        train_split[sym] = [
            b
            for b in bars
            if (start_dt is None or b.timestamp >= start_dt) and b.timestamp < train_end
        ]
        val_split[sym] = [
            b for b in bars if train_end <= b.timestamp < test_start and b.timestamp <= val_end
        ]
        test_split[sym] = [
            b
            for b in bars
            if b.timestamp >= test_start and (end_dt is None or b.timestamp <= end_dt)
        ]

    train_ts = [b.timestamp for bars in train_split.values() for b in bars]
    val_ts = [b.timestamp for bars in val_split.values() for b in bars]
    test_ts = [b.timestamp for bars in test_split.values() for b in bars]

    t_range = (min(train_ts), max(train_ts)) if train_ts else (None, None)
    v_range = (min(val_ts), max(val_ts)) if val_ts else (None, None)
    te_range = (min(test_ts), max(test_ts)) if test_ts else (None, None)

    return TrainValTestSplitResult(
        is_available=True,
        status_reason="Disjoint train/validation/test split successfully constructed.",
        train=train_split,
        validation=val_split,
        test=test_split,
        train_range=t_range,
        validation_range=v_range,
        test_range=te_range,
    )


def split_data_by_research_dates(
    data: dict[str, list[Bar]],
    research_config: ResearchConfig,
) -> dict[str, dict[str, list[Bar]]] | None:
    """Split dataset into 'in_sample' and 'out_of_sample' based on research_config dates."""
    split_date_str = research_config.test_start or research_config.train_end
    if not split_date_str:
        return None

    split_dt = datetime.fromisoformat(split_date_str.replace("Z", "+00:00"))
    if split_dt.tzinfo is None:
        split_dt = split_dt.replace(tzinfo=UTC)

    is_split: dict[str, list[Bar]] = {}
    oos_split: dict[str, list[Bar]] = {}

    for sym, bars in data.items():
        is_split[sym] = [b for b in bars if b.timestamp < split_dt]
        oos_split[sym] = [b for b in bars if b.timestamp >= split_dt]

    return {
        "in_sample": is_split,
        "out_of_sample": oos_split,
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
