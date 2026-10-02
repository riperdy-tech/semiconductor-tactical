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
    data_hashes: dict[str, str] = Field(default_factory=dict)
    strategy_variant: str
    symbols: list[str]
    timeframe: str
    random_seed: int
    output_artifacts: list[str] = Field(default_factory=list)


def create_manifest(
    config: EngineConfig,
    data_hashes: dict[str, str] | None = None,
    data_status: str = "REAL_HISTORICAL",
) -> RunManifest:
    raw_cfg_str = config.model_dump_json()
    cfg_hash = hashlib.sha256(raw_cfg_str.encode("utf-8")).hexdigest()[:16]
    return RunManifest(
        config_hash=cfg_hash,
        data_status=data_status,
        data_hashes=data_hashes or {},
        strategy_variant=config.strategy.variant,
        symbols=config.strategy.universe,
        timeframe=config.strategy.bar_interval,
        random_seed=config.project.random_seed,
    )

