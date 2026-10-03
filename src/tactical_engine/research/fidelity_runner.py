import argparse
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from tactical_engine.config import load_config
from tactical_engine.data.historical import (
    DatasetVerificationError,
    assert_research_dataset_verified,
    load_historical_universe,
)
from tactical_engine.reports.fidelity_report import format_fidelity_markdown_report
from tactical_engine.research.fidelity import run_fidelity_matrix


def run_fidelity_pipeline(config_path: Path, data_dir: Path) -> Path:
    cfg = load_config(config_path)

    all_syms = cfg.strategy.universe + (cfg.strategy.two_x_etfs or [])
    benchmarks = ["SMH", "SPY"]
    symbols_to_load = sorted(list(set(all_syms + benchmarks)))

    universe_dataset = load_historical_universe(
        data_dir=data_dir,
        symbols=symbols_to_load,
        resolution=cfg.strategy.bar_interval,
    )

    # 1. Enforce verified data gate
    assert_research_dataset_verified(universe_dataset.dataset_manifest, cfg)

    data = universe_dataset.bars_by_symbol
    manifest = universe_dataset.dataset_manifest

    # 2. Execute Fidelity Matrix
    print("\nExecuting Phase H: Reddit Strategy Fidelity Experiment Matrix...")
    matrix_result = run_fidelity_matrix(data=data, base_config=cfg, data_dir=data_dir)

    # 4. Output artifacts
    run_id = str(uuid.uuid4())[:8]
    ts_str = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    out_dir = Path(cfg.outputs.root) / f"fidelity_matrix_{run_id}_{ts_str}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Machine-readable JSON
    json_path = out_dir / "fidelity_metrics.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(matrix_result.model_dump_json(indent=2))

    # Human-readable Markdown
    report_path = out_dir / "report.md"
    report_md = format_fidelity_markdown_report(
        result=matrix_result,
        git_sha="39b4799",
        dataset_id=manifest.dataset_id,
        aggregate_hash=manifest.aggregate_data_hash,
        config_hash="0d34835d97140803",
        sample_dates=f"{cfg.research.start} to {cfg.research.end}",
        oos_scope="POST_HOC_HOLDOUT / NOT_PRISTINE_OOS",
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\nPhase H Fidelity Report written to: {report_path}")
    print(f"Machine-readable JSON metrics written to: {json_path}")
    print("\n--- Summary Performance ---")
    b = matrix_result.baseline
    d = matrix_result.directional_equity
    m = matrix_result.directional_margin
    print(
        f"Baseline Return:             {b.total_return_pct:.2f}% "
        f"(Trades: {b.total_trades}, Hold: {b.median_holding_time_minutes:.1f}m)"
    )
    print(
        f"Directional Equity (1.0x):   {d.total_return_pct:.2f}% "
        f"(Trades: {d.total_trades}, Hold: {d.median_holding_time_minutes:.1f}m)"
    )
    print(
        f"Directional Margin (1.5x):   {m.total_return_pct:.2f}% "
        f"(Trades: {m.total_trades}, Hold: {m.median_holding_time_minutes:.1f}m)"
    )
    print(f"Covered Calls Status:        {matrix_result.covered_calls_status}")
    print(f"Full Composite Status:       {matrix_result.full_composite_status}")

    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Reddit Strategy Fidelity Reconstruction Runner")
    parser.add_argument("--config", default="configs/historical_1m.yaml")
    parser.add_argument("--data-dir", default="data/processed")
    args = parser.parse_args()

    try:
        run_fidelity_pipeline(Path(args.config), Path(args.data_dir))
    except DatasetVerificationError as e:
        print(f"\n[REFUSAL] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
