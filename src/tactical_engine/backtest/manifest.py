import hashlib
import subprocess
import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from tactical_engine.config import EngineConfig


def get_git_commit_hash() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return "unknown"


class RunManifest(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at_utc: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    git_commit: str = Field(default_factory=get_git_commit_hash)
    config_hash: str
    data_status: str = "REAL_HISTORICAL"
    dataset_id: str | None = None
    aggregate_data_hash: str | None = None
    data_hashes: dict[str, str] = Field(default_factory=dict)
    strategy_variant: str
    symbols: list[str]
    timeframe: str
    random_seed: int
    research_start: str | None = None
    train_end: str | None = None
    validation_end: str | None = None
    test_start: str | None = None
    research_end: str | None = None
    oos_scope_classification: str = "POST_HOC_HOLDOUT"
    pristine_oos_status: str = "PRISTINE_OOS_UNAVAILABLE"
    output_artifacts: list[str] = Field(default_factory=list)


def create_manifest(
    config: EngineConfig,
    data_hashes: dict[str, str] | None = None,
    data_status: str = "REAL_HISTORICAL",
    dataset_id: str | None = None,
    aggregate_data_hash: str | None = None,
    oos_scope_classification: str = "POST_HOC_HOLDOUT",
    pristine_oos_status: str = "PRISTINE_OOS_UNAVAILABLE",
) -> RunManifest:
    raw_cfg_str = config.model_dump_json()
    cfg_hash = hashlib.sha256(raw_cfg_str.encode("utf-8")).hexdigest()[:16]
    return RunManifest(
        config_hash=cfg_hash,
        data_status=data_status,
        dataset_id=dataset_id,
        aggregate_data_hash=aggregate_data_hash,
        data_hashes=data_hashes or {},
        strategy_variant=config.strategy.variant,
        symbols=config.strategy.universe,
        timeframe=config.strategy.bar_interval,
        random_seed=config.project.random_seed,
        research_start=config.research.start,
        train_end=config.research.train_end,
        validation_end=config.research.validation_end,
        test_start=config.research.test_start,
        research_end=config.research.end,
        oos_scope_classification=oos_scope_classification,
        pristine_oos_status=pristine_oos_status,
    )

