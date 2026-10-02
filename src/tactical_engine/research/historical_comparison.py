import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from tactical_engine.backtest.manifest import create_manifest
from tactical_engine.config import load_config
from tactical_engine.data.historical import (
    HistoricalDataMissingError,
    load_historical_universe,
)
from tactical_engine.research.comparison import run_strategy_comparison
from tactical_engine.research.report_generator import render_comparison_report


def run_historical_comparison(config_path: str, data_dir: str) -> None:
    config = load_config(config_path)
    tradable_symbols = list(
        dict.fromkeys(config.strategy.universe + (config.strategy.two_x_etfs or []))
    )
    # Always load benchmark inputs SMH and SPY for regime evaluation
    symbols_to_load = list(dict.fromkeys(tradable_symbols + ["SMH", "SPY"]))

    data_path = Path(data_dir)
    print("=" * 80)
    print("HISTORICAL 3-VARIANT STRATEGY COMPARISON RUNNER")
    print(f"Data directory: {data_path.resolve()}")
    print(f"Tradable Universe: {tradable_symbols}")
    print("Benchmark Inputs: ['SMH', 'SPY']")
    print(f"Declared resolution: {config.strategy.bar_interval}")
    print("=" * 80)

    try:
        universe_dataset = load_historical_universe(
            data_dir=data_path,
            symbols=symbols_to_load,
            resolution=config.strategy.bar_interval,
        )
    except (HistoricalDataMissingError, ValueError, FileNotFoundError) as e:
        print("\n" + "!" * 80)
        print("HISTORICAL COMPARISON RUNNER REFUSED EXECUTION:")
        print(f"Required historical data inputs are missing or invalid: {e}")
        print("Historical comparison cannot run without verified real historical data.")
        print("Run '.\\run.ps1 doctor-data' to inspect dataset integrity.")
        print("!" * 80)
        sys.exit(1)

    dataset_manifest = universe_dataset.dataset_manifest
    data_status = dataset_manifest.data_status
    is_fixture = data_status == "SYNTHETIC_SAMPLE_FIXTURE"

    if is_fixture:
        print("\n" + "=" * 80)
        print("NOTICE: RUNNING ON SYNTHETIC SAMPLE FIXTURES.")
        print(f"Dataset: {dataset_manifest.dataset_id} (Provider: {dataset_manifest.provider})")
        print("This run validates software mechanics only. It is NOT real historical research.")
        print("=" * 80 + "\n")
    elif data_status == "REAL_HISTORICAL_UNVERIFIED_SOURCE":
        print("\n" + "=" * 80)
        print("NOTICE: RUNNING ON UNVERIFIED LOCAL HISTORICAL CSV DATA.")
        print("Source files have no cryptographically verified provider manifest.")
        print("=" * 80 + "\n")

    print(f"Loaded {len(universe_dataset.bars_by_symbol)} symbols successfully.")
    print(f"Aggregate Data SHA256: {universe_dataset.aggregate_data_hash}")

    # Prepare data hashes for manifest
    data_hashes = {
        sym: prov.file_sha256 for sym, prov in universe_dataset.provenance_by_symbol.items()
    }

    # Run 3-variant comparison + sensitivities
    print("\nRunning 3-variant backtests on identical dataset...")
    comparison_res = run_strategy_comparison(
        data=universe_dataset.bars_by_symbol,
        base_config=config,
    )

    # Manifest
    manifest = create_manifest(
        config=config,
        data_hashes=data_hashes,
        data_status=data_status,
    )

    # Setup isolated run output directory
    timestamp_str = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    run_dir = (
        Path(config.outputs.root)
        / f"historical_comparison_{manifest.run_id[:8]}_{timestamp_str}"
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest.output_artifacts = [
        str(run_dir / "comparison_metrics.json"),
        str(run_dir / "report.md"),
        str(run_dir / "run_manifest.json"),
    ]

    # Save manifest
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2)

    # Save metrics
    with open(run_dir / "comparison_metrics.json", "w", encoding="utf-8") as f:
        json.dump(comparison_res.model_dump(), f, indent=2)

    # Render report
    report_md = render_comparison_report(comparison=comparison_res, config=config)

    # Header banner
    if is_fixture:
        banner = (
            f"# HISTORICAL COMPARISON REPORT (SYNTHETIC FIXTURE RUN)\n\n"
            f"> [!WARNING]\n"
            f"> **DATA STATUS:** SYNTHETIC SAMPLE FIXTURE DATA (`{data_path.resolve()}`)\n"
            f"> This run used generated sample data fixtures. It validates software mechanics "
            f"only and does NOT constitute real historical market research or evidence.\n"
            f"> **AGGREGATE DATA SHA256:** `{universe_dataset.aggregate_data_hash}`\n\n---\n\n"
        )
    else:
        banner = (
            f"# HISTORICAL 3-VARIANT STRATEGY COMPARISON REPORT\n\n"
            f"> **DATA STATUS:** REAL HISTORICAL MARKET DATA (CSV Ingestion)\n"
            f"> **DATA DIRECTORY:** `{data_path.resolve()}`\n"
            f"> **AGGREGATE DATA SHA256:** `{universe_dataset.aggregate_data_hash}`\n\n---\n\n"
        )

    full_report = banner + report_md
    report_file = run_dir / "report.md"
    report_file.write_text(full_report, encoding="utf-8")

    # Also write canonical comparison report to default location if needed
    (Path(config.outputs.root) / "strategy_comparison_historical.md").write_text(
        full_report, encoding="utf-8"
    )

    print("\nHISTORICAL COMPARISON COMPLETE")
    print(f"Run ID: {manifest.run_id}")
    print(f"Literal Clone Return: {comparison_res.literal_clone.total_return_pct:+.2f}%")
    print(f"Risk Controlled Return: {comparison_res.risk_controlled.total_return_pct:+.2f}%")
    print(f"Regime Adapted Return: {comparison_res.regime_adapted.total_return_pct:+.2f}%")
    print(f"Artifacts saved to: {run_dir.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Historical Strategy Comparison Runner")
    parser.add_argument(
        "--config", type=str, default="configs/historical_daily.yaml", help="Path to config YAML"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Directory containing historical CSVs",
    )
    args = parser.parse_args()

    run_historical_comparison(config_path=args.config, data_dir=args.data_dir)


if __name__ == "__main__":
    main()
