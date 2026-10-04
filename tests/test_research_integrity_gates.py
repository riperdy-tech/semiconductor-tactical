from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig, ResearchConfig
from tactical_engine.data.historical import (
    DatasetManifest,
    DatasetVerificationError,
    assert_research_dataset_verified,
    load_dataset_manifest,
)
from tactical_engine.data.models import Bar
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.historical_runner import run_historical_backtest
from tactical_engine.research.comparison import run_strategy_comparison
from tactical_engine.research.falsification import (
    stationary_block_bootstrap,
    strategy_return_bootstrap,
)
from tactical_engine.research.historical_comparison import run_historical_comparison
from tactical_engine.research.report_generator import render_comparison_report
from tactical_engine.research.walk_forward import split_data_train_val_test

# ==============================================================================
# GATE A: DATASET VERIFICATION GATE
# ==============================================================================


def test_a1_synthetic_fixture_refusal():
    manifest = load_dataset_manifest("data/sample_historical")
    assert manifest.data_status == "SYNTHETIC_SAMPLE_FIXTURE"

    with pytest.raises(DatasetVerificationError) as exc_info:
        assert_research_dataset_verified(manifest)
    assert "Only 'REAL_HISTORICAL_VERIFIED'" in str(exc_info.value)

    # When runner is invoked with raise_on_refusal=True on synthetic sample data
    with pytest.raises(DatasetVerificationError):
        run_historical_backtest(
            "configs/historical_daily.yaml", "data/sample_historical", raise_on_refusal=True
        )

    with pytest.raises(DatasetVerificationError):
        run_historical_comparison(
            "configs/historical_daily.yaml", "data/sample_historical", raise_on_refusal=True
        )


def test_a1_cli_main_exit_nonzero(monkeypatch):
    from tactical_engine.historical_runner import main as runner_main
    from tactical_engine.research.historical_comparison import main as comp_main

    monkeypatch.setattr(
        "sys.argv",
        [
            "historical_runner",
            "--data-dir",
            "data/sample_historical",
            "--config",
            "configs/historical_daily.yaml",
        ],
    )
    with pytest.raises(SystemExit) as exc1:
        runner_main()
    assert exc1.value.code != 0

    monkeypatch.setattr(
        "sys.argv",
        [
            "historical_comparison",
            "--data-dir",
            "data/sample_historical",
            "--config",
            "configs/historical_daily.yaml",
        ],
    )
    with pytest.raises(SystemExit) as exc2:
        comp_main()
    assert exc2.value.code != 0


def test_a1_cli_subprocesses_exit_nonzero():
    import subprocess
    import sys

    res1 = subprocess.run(
        [
            sys.executable,
            "-m",
            "tactical_engine.historical_runner",
            "--data-dir",
            "data/sample_historical",
            "--config",
            "configs/historical_daily.yaml",
        ],
        capture_output=True,
        text=True,
    )
    assert res1.returncode != 0
    assert "REFUSED EXECUTION" in res1.stdout

    res2 = subprocess.run(
        [
            sys.executable,
            "-m",
            "tactical_engine.research.historical_comparison",
            "--data-dir",
            "data/sample_historical",
            "--config",
            "configs/historical_daily.yaml",
        ],
        capture_output=True,
        text=True,
    )
    assert res2.returncode != 0
    assert "REFUSED EXECUTION" in res2.stdout


def test_a2_unverified_source_refusal(tmp_path: Path):
    # Directory with no manifest defaults to REAL_HISTORICAL_UNVERIFIED_SOURCE
    manifest = load_dataset_manifest(tmp_path)
    assert manifest.data_status == "REAL_HISTORICAL_UNVERIFIED_SOURCE"
    assert manifest.is_verified_market_data is False

    with pytest.raises(DatasetVerificationError):
        assert_research_dataset_verified(manifest)


def test_a3_verified_source_acceptance():
    manifest = DatasetManifest(
        dataset_id="nasdaq_primary_2014",
        data_status="REAL_HISTORICAL_VERIFIED",
        provider="nasdaq_itch_l3",
        is_verified_market_data=True,
        source_description="Primary historical tick-level market dataset",
        bar_resolution="1d",
    )
    cfg = EngineConfig()
    cfg.strategy.bar_interval = "1d"
    # Should not raise
    assert_research_dataset_verified(manifest, cfg)


def test_a4_no_path_name_spoofing(tmp_path: Path):
    # Creating a folder named "real_verified_historical_market_data"
    spoof_dir = tmp_path / "real_verified_historical_market_data"
    spoof_dir.mkdir()
    # But it contains synthetic manifest
    manifest = DatasetManifest(
        dataset_id="spoofed_dir",
        data_status="SYNTHETIC_SAMPLE_FIXTURE",
        provider="generator",
        is_verified_market_data=False,
    )
    (spoof_dir / "dataset_manifest.json").write_text(manifest.model_dump_json(), encoding="utf-8")

    loaded_manifest = load_dataset_manifest(spoof_dir)
    assert loaded_manifest.data_status == "SYNTHETIC_SAMPLE_FIXTURE"
    with pytest.raises(DatasetVerificationError):
        assert_research_dataset_verified(loaded_manifest)


# ==============================================================================
# GATE B: TRAIN / VALIDATION / TEST SPLIT
# ==============================================================================


def test_b1_b2_b3_train_val_test_splits_disjoint():
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    bars = [
        Bar(
            symbol="MU",
            timestamp=t0 + timedelta(days=i),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000,
        )
        for i in range(100)
    ]
    data = {"MU": bars}

    # Day 0 to 49 (Train), Day 50 to 74 (Validation), Day 75 to 99 (Test)
    research_cfg = ResearchConfig(
        start="2026-01-01T00:00:00+00:00",
        train_end="2026-02-20T00:00:00+00:00",  # Day 50
        validation_end="2026-03-17T00:00:00+00:00",  # Day 75
        test_start="2026-03-17T00:00:00+00:00",  # Day 75
        end="2026-04-11T00:00:00+00:00",
    )

    split_res = split_data_train_val_test(data, research_cfg)
    assert split_res.is_available is True

    train_ts = set(b.timestamp for b in split_res.train["MU"])
    val_ts = set(b.timestamp for b in split_res.validation["MU"])
    test_ts = set(b.timestamp for b in split_res.test["MU"])

    # B1: All 3 splits produced
    assert len(train_ts) > 0
    assert len(val_ts) > 0
    assert len(test_ts) > 0

    # B2: Strictly disjoint sets (no timestamp in more than one partition)
    assert len(train_ts.intersection(val_ts)) == 0
    assert len(train_ts.intersection(test_ts)) == 0
    assert len(val_ts.intersection(test_ts)) == 0

    # B3: Final test partition starts at or after test_start
    test_start_dt = datetime.fromisoformat("2026-03-17T00:00:00+00:00")
    assert all(ts >= test_start_dt for ts in test_ts)


def test_b4_three_variants_produce_train_val_test_metrics():
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    bars = generate_synthetic_bars("MU", num_bars=120, seed=42, start_time=t0)
    data = {"MU": bars}

    cfg = EngineConfig()
    cfg.strategy.universe = ["MU"]
    cfg.research = ResearchConfig(
        train_end=(t0 + timedelta(minutes=50)).isoformat(),
        validation_end=(t0 + timedelta(minutes=80)).isoformat(),
        test_start=(t0 + timedelta(minutes=80)).isoformat(),
    )

    res = run_strategy_comparison(data, cfg)
    assert res.oos_available is True

    # B4: Each of the 3 strategy variants produces train, validation, and test metrics
    for v in ["literal_clone", "risk_controlled", "regime_adapted"]:
        assert v in res.train_metrics
        assert v in res.validation_metrics
        assert v in res.test_metrics
        assert res.train_metrics[v].total_trades >= 0
        assert res.validation_metrics[v].total_trades >= 0
        assert res.test_metrics[v].total_trades >= 0


def test_b5_missing_boundaries_produce_explicit_unavailable_status():
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    bars = generate_synthetic_bars("MU", num_bars=50, seed=42, start_time=t0)
    data = {"MU": bars}

    cfg = EngineConfig()
    cfg.strategy.universe = ["MU"]
    cfg.research = ResearchConfig(train_end="2026-01-01T00:30:00Z")  # Missing val_end, test_start

    res = run_strategy_comparison(data, cfg)
    assert res.oos_available is False
    assert "unavailable" in res.oos_status_reason.lower()
    assert len(res.train_metrics) == 0
    assert len(res.validation_metrics) == 0
    assert len(res.test_metrics) == 0


# ==============================================================================
# GATE D: ROBUSTNESS DIAGNOSTICS & RESAMPLING UNITS
# ==============================================================================


def test_d1_d2_resampling_units_distinguished():
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    bars = generate_synthetic_bars("SMH", num_bars=60, seed=42, start_time=t0)

    # D1: Benchmark return dependence diagnostic
    bb = stationary_block_bootstrap(bars, expected_block_size=10, num_simulations=100, symbol="SMH")
    assert bb.resampling_unit == "benchmark_bar_returns"
    assert bb.diagnostic_name == "Benchmark Return Dependence Diagnostic"
    assert bb.symbol == "SMH"
    assert bb.period_scope == "FULL"

    # D2: Strategy-level return robustness diagnostic
    cfg = EngineConfig()
    cfg.strategy.universe = ["SMH"]
    bt_res = run_backtest({"SMH": bars}, cfg)

    sb = strategy_return_bootstrap(bt_res.trades, initial_cash=100_000.0, num_simulations=100)
    assert sb.resampling_unit == "strategy_daily_returns"
    assert sb.diagnostic_name == "Strategy-Level Return Robustness Diagnostic"
    assert sb.period_scope == "FULL"
    assert "Complete daily trading session return" in sb.observation_definition


def test_d3_complete_session_axis_preserves_inactive_days():
    from tactical_engine.backtest.state import TradeRecord

    t0 = datetime(2026, 1, 5, 10, 0, tzinfo=UTC)  # Monday
    # Create 12 trades on 12 distinct days
    trades = []
    trade_dates = []
    for day_offset in range(12):
        trade_dt = t0 + timedelta(days=day_offset)
        trades.append(
            TradeRecord(
                symbol="MU",
                entry_time=trade_dt,
                entry_price=100.0,
                exit_time=trade_dt + timedelta(hours=2),
                exit_price=105.0,
                quantity=100,
                gross_pnl=500.0,
                net_pnl=500.0,
                exit_reason="TARGET",
            )
        )
        trade_dates.append(trade_dt.strftime("%Y-%m-%d"))

    # Supply an evaluation period of 15 sessions (3 inactive days added)
    extra_dates = [
        (t0 + timedelta(days=20)).strftime("%Y-%m-%d"),
        (t0 + timedelta(days=21)).strftime("%Y-%m-%d"),
        (t0 + timedelta(days=22)).strftime("%Y-%m-%d"),
    ]
    all_sessions = sorted(trade_dates + extra_dates)
    assert len(all_sessions) == 15

    sb = strategy_return_bootstrap(
        trades=trades,
        initial_cash=100_000.0,
        evaluation_dates=all_sessions,
        period_scope="TRAIN",
        num_simulations=100,
    )

    assert sb.period_scope == "TRAIN"
    assert sb.sample_size == 15
    assert sb.active_trading_days == 12
    assert sb.inactive_sessions == 3
    assert sb.is_sufficient_sample is True
    assert sb.prob_positive > 0.90


def test_d5_oos_insufficient_sample_handled():
    # If OOS period has fewer than 10 trades/days
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    bars = generate_synthetic_bars("MU", num_bars=30, seed=42, start_time=t0)
    data = {"MU": bars}

    cfg = EngineConfig()
    cfg.strategy.universe = ["MU"]
    # Very short test period: last 5 bars
    cfg.research = ResearchConfig(
        train_end=(t0 + timedelta(minutes=15)).isoformat(),
        validation_end=(t0 + timedelta(minutes=25)).isoformat(),
        test_start=(t0 + timedelta(minutes=25)).isoformat(),
    )

    res = run_strategy_comparison(data, cfg)
    assert res.oos_available is True
    assert res.oos_strategy_bootstrap is not None
    assert res.oos_strategy_bootstrap.is_sufficient_sample is False
    assert res.oos_strategy_bootstrap.period_scope == "TEST_OOS"
    assert res.strategy_bootstrap.period_scope == "FULL"
    assert res.benchmark_bootstrap.period_scope == "FULL"
    assert res.ticker_exclusion.period_scope == "FULL"
    assert res.strongest_day_exclusion.period_scope == "FULL"
    assert "INSUFFICIENT_SAMPLE" in (res.oos_strategy_bootstrap.insufficient_reason or "")

    report = render_comparison_report(res, cfg)
    assert "INSUFFICIENT_SAMPLE" in report
    assert "FULL SAMPLE" in report or "FULL" in report
    assert "TEST_OOS" in report
    assert "Observation Definition" in report


# ==============================================================================
# GATE E: SENSITIVITY GRID RECONCILIATION
# ==============================================================================


def test_e_sensitivity_grids():
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    bars = generate_synthetic_bars("MU", num_bars=50, seed=42, start_time=t0)
    cfg = EngineConfig()
    cfg.strategy.universe = ["MU"]

    res = run_strategy_comparison({"MU": bars}, cfg)

    # Documented leverage: 1.0x, 1.25x, 1.5x, 2.0x, 3.0x
    expected_levs = {"1.00x", "1.25x", "1.50x", "2.00x", "3.00x"}
    assert set(res.leverage_sensitivity.keys()) == expected_levs

    # Documented costs: 0bps, 5bps, 10bps, 15bps
    expected_costs = {"0bps", "5bps", "10bps", "15bps"}
    assert set(res.cost_sensitivity.keys()) == expected_costs
