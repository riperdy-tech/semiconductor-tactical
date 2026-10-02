from pathlib import Path

from tactical_engine.research.historical_comparison import run_historical_comparison


def test_historical_comparison_generates_outputs(tmp_path: Path):
    # Setup dummy daily CSV data
    symbols = ["MU", "SNDK", "SKHY", "AMD", "USD"]
    for sym in symbols:
        rows = [
            "date,open,high,low,close,volume\n",
            "2024-01-02,100,105,95,102,500000\n",
            "2024-01-03,102,106,98,104,600000\n",
            "2024-01-04,104,107,101,103,550000\n",
            "2024-01-05,103,105,99,101,450000\n",
        ]
        (tmp_path / f"{sym}.csv").write_text("".join(rows), encoding="utf-8")

    run_historical_comparison(
        config_path="configs/historical_daily.yaml",
        data_dir=str(tmp_path),
    )

    canonical_report = Path("reports/strategy_comparison_historical.md")
    assert canonical_report.exists()
    content = canonical_report.read_text(encoding="utf-8")
    assert "HISTORICAL" in content
    assert "Strategy Variant Comparison" in content
    assert "literal_clone" in content
    assert "risk_controlled" in content
    assert "regime_adapted" in content
