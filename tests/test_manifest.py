from tactical_engine.backtest.manifest import create_manifest
from tactical_engine.config import EngineConfig


def test_create_run_manifest():
    cfg = EngineConfig()
    manifest = create_manifest(
        config=cfg,
        data_hashes={"MU": "dummy_hash"},
        dataset_id="massive_stocks_1m_51e9b529de55",
        aggregate_data_hash="51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8",
        oos_scope_classification="POST_HOC_HOLDOUT",
        pristine_oos_status="PRISTINE_OOS_UNAVAILABLE",
    )
    assert manifest.run_id is not None
    assert manifest.config_hash is not None
    assert manifest.strategy_variant == "risk_controlled"
    assert manifest.symbols == ["MU", "SNDK", "SKHY", "AMD"]
    assert manifest.data_status == "REAL_HISTORICAL"
    assert manifest.dataset_id == "massive_stocks_1m_51e9b529de55"
    assert manifest.aggregate_data_hash == (
        "51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8"
    )
    assert manifest.oos_scope_classification == "POST_HOC_HOLDOUT"
    assert manifest.pristine_oos_status == "PRISTINE_OOS_UNAVAILABLE"

    fixture_manifest = create_manifest(
        config=cfg,
        data_hashes={"MU": "dummy_hash"},
        data_status="SYNTHETIC_SAMPLE_FIXTURE",
    )
    assert fixture_manifest.data_status == "SYNTHETIC_SAMPLE_FIXTURE"

