import numpy as np
from tactical_engine.research.sweeps import SweepResult


def calculate_stability_score(sweep_results: list[SweepResult]) -> float:
    """Calculate parameter stability based on return dispersion across neighbor parameters.

    Returns a score between 0.0 (highly fragile) and 1.0 (highly stable).
    """
    if len(sweep_results) <= 1:
        return 1.0

    returns = [r.metrics.total_return_pct for r in sweep_results]
    mean_ret = float(np.mean(returns))
    std_ret = float(np.std(returns))

    if mean_ret == 0:
        return 0.5

    # Coefficient of variation (lower is more stable)
    cv = abs(std_ret / mean_ret)
    # Map to 0-1 scale using exponential decay
    score = float(np.exp(-cv))
    return round(max(0.0, min(1.0, score)), 4)


def render_sweep_table(sweep_results: list[SweepResult]) -> str:
    lines = [
        "| Parameter Set | Return % | Max DD % | Trades | Win Rate |",
        "|---|---|---|---|---|",
    ]
    for r in sweep_results:
        param_desc = ", ".join(f"{k}={v}" for k, v in r.params.items())
        m = r.metrics
        lines.append(
            f"| `{param_desc}` | {m.total_return_pct:.2f}% | "
            f"{m.max_drawdown_pct:.2f}% | {m.total_trades} | {m.win_rate * 100:.1f}% |"
        )
    return "\n".join(lines)
