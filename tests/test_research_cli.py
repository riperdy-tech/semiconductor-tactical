from pathlib import Path

from tactical_engine.config import EngineConfig
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.research.cli import run_full_experiment_matrix


def test_run_full_experiment_matrix(tmp_path):
    bars = generate_synthetic_bars(symbol="MU", num_bars=100, seed=42)
    cfg = EngineConfig()
    cfg.outputs.root = str(tmp_path)

    report_path = run_full_experiment_matrix(
        data={"MU": bars},
        config=cfg,
        output_dir=tmp_path,
    )

    assert Path(report_path).exists()
    content = Path(report_path).read_text(encoding="utf-8")
    assert "# Experiment Matrix & Robustness Report" in content
    assert "Walk-Forward Results" in content
    assert "Parameter Sweep Stability" in content
    assert "Monte Carlo Bootstrap" in content
