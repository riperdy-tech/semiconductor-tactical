import argparse
from pathlib import Path

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.backtest.manifest import create_manifest
from tactical_engine.config import load_config
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.reports.attribution import attribute_pnl_by_ticker
from tactical_engine.reports.metrics import calculate_metrics
from tactical_engine.reports.renderer import render_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="High-Beta Tactical Research Engine")
    parser.add_argument(
        "--config", type=str, default="configs/base.yaml", help="Path to YAML config"
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=200,
        help="Number of synthetic bars per ticker if using fixtures",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Loaded config: {args.config} (variant={config.strategy.variant})")

    # Generate synthetic fixtures for symbols
    data = {
        sym: generate_synthetic_bars(
            symbol=sym, num_bars=args.bars, seed=config.project.random_seed + i
        )
        for i, sym in enumerate(config.strategy.universe)
    }

    manifest = create_manifest(config)
    result = run_backtest(data, config)
    metrics = calculate_metrics(result)
    attribution = attribute_pnl_by_ticker(result)

    report_md = render_markdown_report(metrics, manifest, attribution)

    out_dir = Path(config.outputs.root)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / f"run_{manifest.run_id[:8]}.md"
    report_file.write_text(report_md, encoding="utf-8")

    print(
        f"Backtest completed: {metrics.total_trades} trades. "
        f"Final Equity: ${metrics.final_equity:,.2f}"
    )
    print(f"Report generated: {report_file}")


if __name__ == "__main__":
    main()
