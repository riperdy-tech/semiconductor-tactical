from pathlib import Path

import pytest
from pydantic import ValidationError

from tactical_engine.config import EngineConfig, load_config


def test_load_base_config():
    config_path = Path("configs/base.yaml")
    config = load_config(config_path)
    assert isinstance(config, EngineConfig)
    assert config.project.name == "high-beta-tactical"
    assert config.strategy.variant == "risk_controlled"
    assert "MU" in config.strategy.universe
    assert config.signals.pullback_zscore == -1.5
    assert config.exits.family == "atr"
    assert config.portfolio.max_gross_leverage == 1.0
    assert config.costs.equity_slippage_bps == 5.0


def test_config_validation_error(tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("strategy:\n  variant: unknown_variant\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config(bad_yaml)
