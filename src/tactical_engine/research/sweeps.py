import itertools
from typing import Any
from pydantic import BaseModel, Field
from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar
from tactical_engine.reports.metrics import PerformanceMetrics, calculate_metrics


class ParameterGrid(BaseModel):
    pullback_zscores: list[float] = Field(default_factory=lambda: [-1.0, -1.5, -2.0])
    target_atrs: list[float] = Field(default_factory=lambda: [1.0, 1.5])
    stop_atrs: list[float] = Field(default_factory=lambda: [1.0, 1.5])
    max_hold_minutes: list[int] = Field(default_factory=lambda: [60, 120])


class SweepResult(BaseModel):
    params: dict[str, Any]
    metrics: PerformanceMetrics


def run_parameter_sweep(
    data: dict[str, list[Bar]],
    base_config: EngineConfig,
    grid: ParameterGrid,
) -> list[SweepResult]:
    combinations = list(
        itertools.product(
            grid.pullback_zscores,
            grid.target_atrs,
            grid.stop_atrs,
            grid.max_hold_minutes,
        )
    )

    results: list[SweepResult] = []

    for zscore, target_atr, stop_atr, max_hold in combinations:
        # Clone base config with new parameters
        cfg_dict = base_config.model_dump()
        cfg_dict["signals"]["pullback_zscore"] = zscore
        cfg_dict["exits"]["target_atr"] = target_atr
        cfg_dict["exits"]["stop_atr"] = stop_atr
        cfg_dict["exits"]["max_hold_minutes"] = max_hold

        modified_cfg = EngineConfig.model_validate(cfg_dict)
        backtest_res = run_backtest(data, modified_cfg)
        metrics = calculate_metrics(backtest_res)

        results.append(
            SweepResult(
                params={
                    "pullback_zscore": zscore,
                    "target_atr": target_atr,
                    "stop_atr": stop_atr,
                    "max_hold_minutes": max_hold,
                },
                metrics=metrics,
            )
        )

    return results
