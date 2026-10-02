from tactical_engine.config import EngineConfig
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.research.comparison import run_strategy_comparison
from tactical_engine.research.report_generator import render_comparison_report


def test_render_comparison_report():
    bars = generate_synthetic_bars(symbol="MU", num_bars=80, seed=42)
    cfg = EngineConfig()
    comparison = run_strategy_comparison(data={"MU": bars}, base_config=cfg)

    report_md = render_comparison_report(comparison=comparison, config=cfg)
    assert "# Strategy Comparison Research Report" in report_md
    assert "literal_clone" in report_md
    assert "risk_controlled" in report_md
    assert "regime_adapted" in report_md
    assert "Cost Sensitivity" in report_md
    assert "Leverage Sensitivity" in report_md
    assert "Evidence Classification" in report_md
