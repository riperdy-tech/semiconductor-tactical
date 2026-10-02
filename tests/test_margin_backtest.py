from datetime import UTC, datetime

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.reports.metrics import calculate_metrics


def test_margin_interest_accrual_and_metrics():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars(symbol="MU", num_bars=150, start_time=t0, seed=42)

    cfg = EngineConfig()
    cfg.portfolio.max_gross_leverage = 2.0
    cfg.portfolio.max_symbol_weight = 1.5  # allow leverage up to 1.5x on single name
    cfg.costs.margin_rate_annual = 0.10  # 10% annual margin interest

    result = run_backtest(data={"MU": bars}, config=cfg)
    metrics = calculate_metrics(result)

    assert hasattr(result, "margin_interest_paid")
    assert hasattr(metrics, "margin_interest_paid")
    assert hasattr(metrics, "peak_margin_debt")
    assert hasattr(metrics, "margin_call_count")
    assert hasattr(metrics, "forced_liquidation_count")
