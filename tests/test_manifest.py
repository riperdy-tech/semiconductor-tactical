from tactical_engine.backtest.manifest import create_manifest
from tactical_engine.config import EngineConfig


def test_create_run_manifest():
    cfg = EngineConfig()
    manifest = create_manifest(config=cfg, data_hashes={"MU": "dummy_hash"})
    assert manifest.run_id is not None
    assert manifest.config_hash is not None
    assert manifest.strategy_variant == "risk_controlled"
    assert manifest.symbols == ["MU", "SNDK", "SKHY", "AMD"]
    assert manifest.data_status == "REAL_HISTORICAL"

    fixture_manifest = create_manifest(
        config=cfg,
        data_hashes={"MU": "dummy_hash"},
        data_status="SYNTHETIC_SAMPLE_FIXTURE",
    )
    assert fixture_manifest.data_status == "SYNTHETIC_SAMPLE_FIXTURE"

