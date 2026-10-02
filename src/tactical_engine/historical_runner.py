import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.backtest.manifest import create_manifest
from tactical_engine.config import load_config
from tactical_engine.data.historical import (
    HistoricalDataMissingError,
    load_historical_universe,
)
from tactical_engine.reports.attribution import attribute_pnl_by_ticker
from tactical_engine.reports.metrics import calculate_metrics
from tactical_engine.reports.renderer import render_markdown_report


def run_historical_backtest(config_path: str, data_dir: str) -> None:
    config = load_config(config_path)
    symbols = config.strategy.universe
    if config.strategy.two_x_etfs:
        symbols = symbols + config.strategy.two_x_etfs

    data_path = Path(data_dir)
    print("=" * 80)
    print("HISTORICAL MARKET DATA RESEARCH ENGINE")
    print(f"Data directory: {data_path.resolve()}")
    print(f"Universe: {symbols}")
    print("=" * 80)

    try:
        universe_dataset = load_historical_universe(
            data_dir=data_path,
            symbols=symbols,
            resolution=config.strategy.bar_interval,
        )
    except (HistoricalDataMissingError, ValueError, FileNotFoundError) as e:
        print("\n" + "!" * 80)
        print("HISTORICAL RUNNER REFUSED EXECUTION:")
        print(f"Required historical data inputs are missing or invalid: {e}")
        print("Historical research cannot run without verified real historical data.")
        print("Run '.\\run.ps1 doctor-data' to check dataset completeness.")
        print("!" * 80)
        sys.exit(1)

    print(f"Loaded {len(universe_dataset.bars_by_symbol)} symbols successfully.")
    print(f"Aggregate Data SHA256: {universe_dataset.aggregate_data_hash}")

    # Prepare data hashes for manifest
    data_hashes = {
        sym: prov.file_sha256 for sym, prov in universe_dataset.provenance_by_symbol.items()
    }

    # Execute backtest
    result = run_backtest(data=universe_dataset.bars_by_symbol, config=config)
    metrics = calculate_metrics(result)
    attribution = attribute_pnl_by_ticker(result)

    # Create run manifest
    manifest = create_manifest(config=config, data_hashes=data_hashes)

    # Setup isolated run output directory
    timestamp_str = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(config.outputs.root) / f"historical_{manifest.run_id[:8]}_{timestamp_str}"
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest.output_artifacts = [
        str(run_dir / "metrics.json"),
        str(run_dir / "report.md"),
        str(run_dir / "trades.json"),
        str(run_dir / "run_manifest.json"),
    ]

    # Save manifest
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2)

    # Save metrics
    with open(run_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics.model_dump(), f, indent=2)

    # Save trades
    with open(run_dir / "trades.json", "w", encoding="utf-8") as f:
        trades_data = [t.model_dump(mode="json") for t in result.trades]
        json.dump(trades_data, f, indent=2)

    # Render report
    report_md = render_markdown_report(
        metrics=metrics, manifest=manifest, ticker_attribution=attribution
    )
    # Prepend Historical Market Data Banner
    historical_header = (
        f"# HISTORICAL MARKET DATA RESEARCH REPORT\n\n"
        f"> **DATA STATUS:** REAL HISTORICAL MARKET DATA (CSV Ingestion)\n"
        f"> **DATA DIRECTORY:** `{data_path.resolve()}`\n"
        f"> **AGGREGATE DATA SHA256:** `{universe_dataset.aggregate_data_hash}`\n\n---\n\n"
    )
    full_report = historical_header + report_md
    report_file = run_dir / "report.md"
    report_file.write_text(full_report, encoding="utf-8")

    print("\nHISTORICAL RESEARCH RUN COMPLETE")
    print(f"Run ID: {manifest.run_id}")
    print(f"Trades Executed: {len(result.trades)}")
    print(f"Final Equity: ${result.final_equity:,.2f} ({metrics.total_return_pct:+.2f}%)")
    print(f"Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
    print(f"Artifacts saved to: {run_dir.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run historical market data backtest")
    parser.add_argument(
        "--config", type=str, default="configs/base.yaml", help="Path to config YAML"
    )
    parser.add_argument(
        "--data-dir", type=str, default="data/processed", help="Path to historical data directory"
    )
    args = parser.parse_args()

    run_historical_backtest(config_path=args.config, data_dir=args.data_dir)


if __name__ == "__main__":
    main()
