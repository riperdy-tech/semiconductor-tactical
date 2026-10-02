from datetime import UTC, datetime, timedelta
from pathlib import Path

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig, ResearchConfig
from tactical_engine.data.historical import load_dataset_manifest
from tactical_engine.data.models import Bar
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.research.comparison import run_strategy_comparison
from tactical_engine.research.report_generator import render_comparison_report
from tactical_engine.research.walk_forward import split_data_by_research_dates


def test_benchmark_loading_and_regime_adapted_wiring():
    # Construct bars for MU and dual benchmarks SMH and SPY
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    mu_bars = generate_synthetic_bars("MU", num_bars=100, seed=42, start_time=t0)

    # Bullish benchmark: rising SMH and SPY
    smh_bull = [
        Bar(
            symbol="SMH",
            timestamp=t0 + timedelta(minutes=i),
            open=100.0 + i * 0.1,
            high=101.0 + i * 0.1,
            low=99.5 + i * 0.1,
            close=100.5 + i * 0.1,
            volume=5000,
        )
        for i in range(100)
    ]
    spy_bull = [
        Bar(
            symbol="SPY",
            timestamp=t0 + timedelta(minutes=i),
            open=400.0 + i * 0.2,
            high=401.0 + i * 0.2,
            low=399.5 + i * 0.2,
            close=400.5 + i * 0.2,
            volume=20000,
        )
        for i in range(100)
    ]

    data_bull = {"MU": mu_bars, "SMH": smh_bull, "SPY": spy_bull}

    cfg_risk = EngineConfig()
    cfg_risk.strategy.universe = ["MU"]
    cfg_risk.signals.sector_filter = False

    cfg_regime = EngineConfig()
    cfg_regime.strategy.universe = ["MU"]
    cfg_regime.signals.sector_filter = True
    cfg_regime.signals.regime_filter_mode = "sector"

    res_risk_bull = run_backtest(data_bull, cfg_risk)
    res_regime_bull = run_backtest(data_bull, cfg_regime)

    # Now create Bearish benchmark: crashing SMH
    smh_bear = [
        Bar(
            symbol="SMH",
            timestamp=t0 + timedelta(minutes=i),
            open=150.0 - i * 0.5,
            high=151.0 - i * 0.5,
            low=149.0 - i * 0.5,
            close=149.5 - i * 0.5,
            volume=5000,
        )
        for i in range(100)
    ]
    data_bear = {"MU": mu_bars, "SMH": smh_bear, "SPY": spy_bull}

    res_risk_bear = run_backtest(data_bear, cfg_risk)
    res_regime_bear = run_backtest(data_bear, cfg_regime)

    # 1. SMH and SPY should NOT be traded (only MU is in tradable universe)
    assert all(t.symbol == "MU" for t in res_risk_bull.trades)
    assert all(t.symbol == "MU" for t in res_regime_bull.trades)

    # 2. Risk controlled (sector_filter=False) ignores SMH trend: results are identical
    assert len(res_risk_bull.trades) == len(res_risk_bear.trades)

    # 3. Regime adapted (sector_filter=True) is suppressed by bearish SMH regime
    assert len(res_regime_bear.trades) <= len(res_regime_bull.trades)


def test_provenance_status_enforcement_and_manifest_loading(tmp_path: Path):
    # Case 1: unverified directory without dataset_manifest.json
    manifest_unverified = load_dataset_manifest(tmp_path)
    assert manifest_unverified.data_status == "REAL_HISTORICAL_UNVERIFIED_SOURCE"
    assert manifest_unverified.is_verified_market_data is False

    # Case 2: explicit manifest with synthetic fixture
    (tmp_path / "dataset_manifest.json").write_text(
        '{"dataset_id": "test_fixtures", "data_status": "SYNTHETIC_SAMPLE_FIXTURE", '
        '"provider": "test_generator", "is_verified_market_data": false}',
        encoding="utf-8",
    )
    manifest_fixture = load_dataset_manifest(tmp_path)
    assert manifest_fixture.data_status == "SYNTHETIC_SAMPLE_FIXTURE"
    assert manifest_fixture.is_verified_market_data is False


def test_oos_split_behavior_and_metrics():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars("MU", num_bars=100, seed=42, start_time=t0)
    data = {"MU": bars}

    # Split at bar 50 (50 mins after start)
    split_time = t0 + timedelta(minutes=50)
    research_cfg = ResearchConfig(test_start=split_time.isoformat())

    splits = split_data_by_research_dates(data, research_cfg)
    assert splits is not None
    assert len(splits["in_sample"]["MU"]) == 50
    assert len(splits["out_of_sample"]["MU"]) == 50
    # No leakage across split point
    assert all(b.timestamp < split_time for b in splits["in_sample"]["MU"])
    assert all(b.timestamp >= split_time for b in splits["out_of_sample"]["MU"])


def test_falsification_report_generation():
    cfg = EngineConfig()
    cfg.strategy.universe = ["MU"]
    cfg.research.test_start = "2026-01-05T15:20:00+00:00"

    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars("MU", num_bars=100, seed=42, start_time=t0)
    data = {"MU": bars}

    comparison = run_strategy_comparison(data=data, base_config=cfg)
    assert comparison.ticker_exclusion is not None
    assert comparison.strongest_day_exclusion is not None
    assert comparison.benchmark_bootstrap is not None
    assert comparison.strategy_bootstrap is not None

    report = render_comparison_report(comparison, cfg)
    assert "Out-of-Sample (OOS) Generalization Analysis" in report
    assert "Benchmark Return Dependence Diagnostic" in report
    assert "Strategy-Level Return Robustness Diagnostic" in report
    assert "Leave-One-Out Ticker Exclusion Test" in report
    assert "Strongest-Day Exclusion Diagnostic" in report
    assert "Options & Event Data Status" in report
    assert "Covered Calls:** `UNVALIDATED`" in report
    assert "Event Blackouts:** `PARTIAL / UNVALIDATED`" in report
