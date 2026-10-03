from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    name: str = "high-beta-tactical"
    timezone_report: str = "America/New_York"
    random_seed: int = 42


class StrategyConfig(BaseModel):
    variant: Literal[
        "literal_clone",
        "risk_controlled",
        "regime_adapted",
        "current_mechanical_pullback_baseline",
        "directional_fidelity_reconstruction",
    ] = "risk_controlled"
    universe: list[str] = Field(default_factory=lambda: ["MU", "SNDK", "SKHY", "AMD"])
    two_x_etfs: list[str] = Field(default_factory=list)
    bar_interval: str = "1m"


class SignalConfig(BaseModel):
    signal_family: Literal["pullback_zscore", "directional_fidelity"] = "pullback_zscore"
    pullback_zscore: float = -1.5
    trend_window: int = 60
    sector_filter: bool = True
    relative_volume_filter: bool = True
    event_filter: bool = True
    regime_filter_mode: Literal["none", "sector", "broad", "combined"] = "sector"
    # Directional fidelity parameters (HYPOTHESIS / ASSUMPTION deterministic proxies)
    pullback_min_pct: float = 0.005
    pullback_max_pct: float = 0.030
    stabilization_threshold: float = 0.35
    swing_target_atr: float = 2.5
    swing_stop_atr: float = 1.5
    order_execution_style: Literal["market", "stop_limit"] = "stop_limit"


class ExitConfig(BaseModel):
    family: Literal["fixed_pct", "atr", "vwap", "time"] = "atr"
    target_pct: float = 0.015
    stop_pct: float = 0.015
    target_atr: float = 1.0
    stop_atr: float = 1.0
    max_hold_minutes: int = 120


class PortfolioConfig(BaseModel):
    initial_cash: float = 100_000.0
    max_symbol_weight: float = 0.25
    max_gross_leverage: float = 1.0
    max_layers: int = 2
    risk_per_trade_pct: float = 0.25


class CostConfig(BaseModel):
    equity_commission_bps: float = 0.0
    equity_slippage_bps: float = 5.0
    option_slippage_bps: float = 10.0
    market_impact_bps_per_1pct_volume: float = 10.0
    margin_rate_annual: float = 0.0


class OptionConfig(BaseModel):
    enabled: bool = False
    max_dte: int = 14
    min_dte: int = 1
    moneyness: Literal["otm", "atm", "itm"] = "otm"
    repurchase_rule: Literal["pullback", "time", "profit", "expiration"] = "pullback"


class ResearchConfig(BaseModel):
    start: str | None = None
    end: str | None = None
    train_end: str | None = None
    validation_end: str | None = None
    test_start: str | None = None


class OutputConfig(BaseModel):
    root: str = "reports"


class EngineConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    signals: SignalConfig = Field(default_factory=SignalConfig)
    exits: ExitConfig = Field(default_factory=ExitConfig)
    portfolio: PortfolioConfig = Field(default_factory=PortfolioConfig)
    costs: CostConfig = Field(default_factory=CostConfig)
    options: OptionConfig = Field(default_factory=OptionConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    outputs: OutputConfig = Field(default_factory=OutputConfig)


def load_config(path: str | Path) -> EngineConfig:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return EngineConfig.model_validate(data)
