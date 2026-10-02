import argparse
from pathlib import Path

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.backtest.manifest import create_manifest
from tactical_engine.config import EngineConfig, load_config
from tactical_engine.data.models import Bar
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.research.bootstrap import (
    bootstrap_trade_returns,
    run_random_entry_control,
)
from tactical_engine.research.diagnostics import (
    calculate_stability_score,
    render_sweep_table,
)
from tactical_engine.research.sweeps import ParameterGrid, run_parameter_sweep
from tactical_engine.research.walk_forward import run_walk_forward


def run_full_experiment_matrix(
    data: dict[str, list[Bar]],
    config: EngineConfig,
    output_dir: Path | str = "reports",
) -> str:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    manifest = create_manifest(config)

    # 1. Base Backtest
    base_res = run_backtest(data, config)

    # 2. Walk-Forward Evaluation
    wf_res = run_walk_forward(data, config, train_ratio=0.5, val_ratio=0.25)

    # 3. Parameter Sweep
    grid = ParameterGrid(
        pullback_zscores=[-1.0, -1.5, -2.0],
        target_atrs=[1.0, 1.5],
        stop_atrs=[1.0, 1.5],
        max_hold_minutes=[60, 120],
    )
    sweep_results = run_parameter_sweep(data, config, grid)
    stability_score = calculate_stability_score(sweep_results)
    sweep_table = render_sweep_table(sweep_results[:6])  # show top sample

    # 4. Monte Carlo Bootstrap on baseline trades
    boot_dist = bootstrap_trade_returns(base_res.trades, num_simulations=500)

    # 5. Random Entry Control
    random_res = run_random_entry_control(data, config, target_trades=base_res.total_trades)

    c0 = config.portfolio.initial_cash
    base_ret = ((base_res.final_equity - c0) / c0 * 100) if c0 > 0 else 0.0
    rand_ret = ((random_res.final_equity - c0) / c0 * 100) if c0 > 0 else 0.0

    report_lines = [
        "# Experiment Matrix & Robustness Report",
        "",
        f"- **Run ID:** `{manifest.run_id}`",
        f"- **Strategy Variant:** `{config.strategy.variant}`",
        f"- **Symbols:** {', '.join(config.strategy.universe)}",
        f"- **Parameter Stability Score:** `{stability_score:.2f}` "
        "(1.0 = highly stable, 0.0 = fragile)",
        "",
        "## Walk-Forward Results",
        "| Split | Return % | Max DD % | Trades | Win Rate |",
        "|---|---|---|---|---|",
        f"| Train (In-Sample) | {wf_res.train_metrics.total_return_pct:.2f}% | "
        f"{wf_res.train_metrics.max_drawdown_pct:.2f}% | {wf_res.train_metrics.total_trades} | "
        f"{wf_res.train_metrics.win_rate * 100:.1f}% |",
        f"| Validation | {wf_res.val_metrics.total_return_pct:.2f}% | "
        f"{wf_res.val_metrics.max_drawdown_pct:.2f}% | {wf_res.val_metrics.total_trades} | "
        f"{wf_res.val_metrics.win_rate * 100:.1f}% |",
        f"| Untouched Test (Out-of-Sample) | {wf_res.test_metrics.total_return_pct:.2f}% | "
        f"{wf_res.test_metrics.max_drawdown_pct:.2f}% | {wf_res.test_metrics.total_trades} | "
        f"{wf_res.test_metrics.win_rate * 100:.1f}% |",
        "",
        "## Monte Carlo Bootstrap (95% Confidence Interval)",
        f"- **Bootstrap Median Mean P&L:** ${boot_dist.median:,.2f}",
        f"- **95% Confidence Interval:** [${boot_dist.ci_lower:,.2f}, ${boot_dist.ci_upper:,.2f}]",
        f"- **Simulations:** {boot_dist.num_simulations}",
        "",
        "## Controls Comparison",
        "| Strategy | Return % | Trades | Final Equity |",
        "|---|---|---|---|",
        f"| Baseline Strategy | {base_ret:.2f}% | "
        f"{base_res.total_trades} | ${base_res.final_equity:,.2f} |",
        f"| Random Entry Control | {rand_ret:.2f}% | "
        f"{random_res.total_trades} | ${random_res.final_equity:,.2f} |",
        "",
        "## Parameter Sweep Stability Sample",
        sweep_table,
    ]

    report_content = "\n".join(report_lines)
    report_file = out_path / f"experiment_matrix_{manifest.run_id[:8]}.md"
    report_file.write_text(report_content, encoding="utf-8")
    return str(report_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Full Robustness & Experiment Matrix")
    parser.add_argument(
        "--config", type=str, default="configs/base.yaml", help="Path to YAML config"
    )
    parser.add_argument("--bars", type=int, default=200, help="Number of bars per symbol")
    args = parser.parse_args()

    config = load_config(args.config)
    data = {
        sym: generate_synthetic_bars(
            symbol=sym, num_bars=args.bars, seed=config.project.random_seed + i
        )
        for i, sym in enumerate(config.strategy.universe)
    }

    report_path = run_full_experiment_matrix(data, config, output_dir=config.outputs.root)
    print(f"Full experiment matrix completed! Report written to: {report_path}")


if __name__ == "__main__":
    main()
