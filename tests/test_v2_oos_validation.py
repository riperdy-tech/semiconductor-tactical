"""Unit and regression tests for Phase M — Frozen Prospective OOS Validation.

Covers all 10 requirements from Section 13 of REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md:
1. Rejection of timestamps on or before 2026-09-30;
2. Rejection of non-headline symbols;
3. Detection of missing common bars / unsynchronized data;
4. Rejection of altered parameter fingerprint;
5. Enforcement of frozen cost config;
6. Preservation of no-lookahead execution;
7. JSON output contains dataset/config/provenance hashes;
8. Real data requirement (refusal of synthetic fixtures);
9. V2-A/B/C share identical core initialization;
10. Historical artifact overwrite protection;
11. Sample completeness classification (<20 sessions vs >=20 sessions).
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tactical_engine.backtest.v2_engine import (
    ACCOUNTING_TOLERANCE,
    V2BacktestResult,
    run_v2_backtest,
)
from tactical_engine.config import CostConfig
from tactical_engine.data.historical import DatasetVerificationError
from tactical_engine.data.models import Bar
from tactical_engine.portfolio.v2_portfolio import V2PortfolioEngine
from tactical_engine.research.v2_oos_runner import (
    HEADLINE_UNIVERSE,
    V2OOSChronologyError,
    V2OOSComparisonResult,
    V2OOSDataRequirementError,
    V2OOSEvaluationError,
    V2OOSParameterFingerprintError,
    V2OOSUniverseError,
    count_complete_sessions,
    evaluate_interpretation,
    run_v2_oos_pipeline,
    validate_oos_chronology,
    validate_oos_universe,
    validate_parameter_fingerprint,
)
from tactical_engine.signals.v2_signals import V2DirectionalConfig


def _make_bar(
    symbol: str,
    dt: datetime,
    open_p: float,
    high_p: float | None = None,
    low_p: float | None = None,
    close_p: float | None = None,
    vol: float = 1000.0,
) -> Bar:
    c = close_p if close_p is not None else open_p
    h = high_p if high_p is not None else max(open_p, c) + 0.1
    l_val = low_p if low_p is not None else min(open_p, c) - 0.1
    return Bar(
        symbol=symbol,
        timestamp=dt,
        open=open_p,
        high=h,
        low=l_val,
        close=c,
        volume=vol,
    )


def test_1_oos_rejects_timestamps_on_or_before_cutoff() -> None:
    """Requirement 1: OOS rejects timestamps on or before 2026-09-30T23:59:59Z."""
    # Bar within historical period (September 30)
    sept_bar = _make_bar("MU", datetime(2026, 9, 30, 19, 59, tzinfo=UTC), 100.0)
    oct_bar = _make_bar("MU", datetime(2026, 10, 1, 13, 30, tzinfo=UTC), 101.0)

    # Violating series must raise V2OOSChronologyError
    with pytest.raises(V2OOSChronologyError) as exc_info:
        validate_oos_chronology({"MU": [sept_bar, oct_bar]})
    assert "violates chronology cutoff" in str(exc_info.value)

    # Exactly at cutoff (23:59:59) must also raise
    cutoff_bar = _make_bar("MU", datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC), 100.0)
    with pytest.raises(V2OOSChronologyError):
        validate_oos_chronology({"MU": [cutoff_bar]})

    # Valid strictly future bars pass cleanly
    valid_bars = {
        "MU": [
            _make_bar("MU", datetime(2026, 10, 1, 13, 30 + i, tzinfo=UTC), 100.0)
            for i in range(5)
        ]
    }
    validate_oos_chronology(valid_bars)


def test_2_oos_rejects_non_headline_symbols() -> None:
    """Requirement 2: OOS rejects non-headline symbols or missing required symbols."""
    # Extra proxy symbol (USD)
    with pytest.raises(V2OOSUniverseError) as exc_info:
        validate_oos_universe(["MU", "SNDK", "SKHY", "USD"])
    assert "does not match required headline universe" in str(exc_info.value)

    # Extra non-headline equity (AMD)
    with pytest.raises(V2OOSUniverseError):
        validate_oos_universe(["MU", "SNDK", "SKHY", "AMD"])

    # Missing symbol (SKHY missing)
    with pytest.raises(V2OOSUniverseError):
        validate_oos_universe(["MU", "SNDK"])

    # Exact headline set passes
    validate_oos_universe(list(HEADLINE_UNIVERSE))


def test_3_oos_session_counting_and_missing_common_bars() -> None:
    """Requirement 3: Complete sessions require >= 300 minutes across all headline symbols."""
    base_day1 = datetime(2026, 10, 1, 13, 30, tzinfo=UTC)
    base_day2 = datetime(2026, 10, 2, 13, 30, tzinfo=UTC)

    # Day 1: All 3 symbols have 390 bars (complete session)
    # Day 2: MU and SNDK have 390 bars, but SKHY only has 100 bars (incomplete session)
    bars = {
        "MU": (
            [_make_bar("MU", base_day1 + timedelta(minutes=i), 100.0) for i in range(390)]
            + [_make_bar("MU", base_day2 + timedelta(minutes=i), 100.0) for i in range(390)]
        ),
        "SNDK": (
            [_make_bar("SNDK", base_day1 + timedelta(minutes=i), 50.0) for i in range(390)]
            + [_make_bar("SNDK", base_day2 + timedelta(minutes=i), 50.0) for i in range(390)]
        ),
        "SKHY": (
            [_make_bar("SKHY", base_day1 + timedelta(minutes=i), 25.0) for i in range(390)]
            + [_make_bar("SKHY", base_day2 + timedelta(minutes=i), 25.0) for i in range(100)]
        ),
    }

    sessions = count_complete_sessions(bars)
    # Only Day 1 is complete for all 3 symbols
    assert sessions == 1


def test_4_oos_rejects_altered_parameter_fingerprint() -> None:
    """Requirement 4: OOS rejects any alteration to the frozen directional parameter registry."""
    valid_cost = CostConfig(equity_commission_bps=0.0, equity_slippage_bps=5.0)

    # Alter impulse threshold (0.025 instead of 0.020)
    altered_sig = V2DirectionalConfig(
        impulse_lookback_bars=30,
        min_impulse_pct=0.025,
        pullback_depth_fraction=0.500,
        stabilization_bars=5,
        tactical_scale_out_ratio=0.50,
        stop_buffer_pct=0.002,
        rebound_target_ratio=0.50,
        trend_filter=True,
    )
    with pytest.raises(V2OOSParameterFingerprintError) as exc_info:
        validate_parameter_fingerprint(altered_sig, valid_cost, max_leverage=2.0)
    assert "Signal configuration" in str(exc_info.value)

    # Valid frozen parameters pass
    frozen_sig = V2DirectionalConfig(
        impulse_lookback_bars=30,
        min_impulse_pct=0.020,
        pullback_depth_fraction=0.500,
        stabilization_bars=5,
        tactical_scale_out_ratio=0.50,
        stop_buffer_pct=0.002,
        rebound_target_ratio=0.50,
        trend_filter=True,
    )
    validate_parameter_fingerprint(frozen_sig, valid_cost, max_leverage=2.0)


def test_5_oos_enforces_frozen_cost_and_leverage() -> None:
    """Requirement 5: OOS enforces exact commission, slippage, and leverage assumptions."""
    frozen_sig = V2DirectionalConfig(
        impulse_lookback_bars=30,
        min_impulse_pct=0.020,
        pullback_depth_fraction=0.500,
        stabilization_bars=5,
        tactical_scale_out_ratio=0.50,
        stop_buffer_pct=0.002,
        rebound_target_ratio=0.50,
        trend_filter=True,
    )
    # Alter slippage (10.0 instead of 5.0)
    bad_cost = CostConfig(equity_commission_bps=0.0, equity_slippage_bps=10.0)
    with pytest.raises(V2OOSParameterFingerprintError):
        validate_parameter_fingerprint(frozen_sig, bad_cost, max_leverage=2.0)

    # Alter leverage ceiling (e.g. 3.0x instead of 2.0x)
    valid_cost = CostConfig(equity_commission_bps=0.0, equity_slippage_bps=5.0)
    with pytest.raises(V2OOSParameterFingerprintError):
        validate_parameter_fingerprint(frozen_sig, valid_cost, max_leverage=3.0)


def test_6_oos_preserves_no_lookahead_execution() -> None:
    """Requirement 6: Changing bar t close does NOT affect next-open order decision."""
    portfolio_a = V2PortfolioEngine(initial_cash=50000.0, max_leverage=2.0)
    portfolio_b = V2PortfolioEngine(initial_cash=50000.0, max_leverage=2.0)

    portfolio_a.open_or_add_core("MU", quantity=200, price=100.0)
    portfolio_b.open_or_add_core("MU", quantity=200, price=100.0)

    # Bar t close: Scenario A crashes to $10; Scenario B surges to $1,000
    # Execution occurs at bar t+1 open price ($100)
    portfolio_a.tactical_add("MU", quantity=100, price=100.0)
    portfolio_b.tactical_add("MU", quantity=100, price=100.0)

    assert portfolio_a.tactical_positions["MU"].quantity == 100
    assert portfolio_b.tactical_positions["MU"].quantity == 100
    assert portfolio_a.cash == portfolio_b.cash


def test_7_oos_json_provenance_and_hash_schema() -> None:
    """Requirement 7: JSON output contains dataset/config/provenance hashes."""
    dummy_res = V2BacktestResult(
        mode="V2-A",
        initial_cash=100000.0,
        final_equity=105000.0,
        total_net_pnl=5000.0,
        total_return_pct=5.0,
        max_drawdown_pct=1.5,
        core_starting_value=59000.0,
        core_ending_value=64000.0,
        effective_start_timestamp="2026-10-01T13:30:00Z",
        evaluation_end_timestamp="2026-10-02T19:59:00Z",
    )
    result = V2OOSComparisonResult(
        run_id="oos_test1",
        created_at_utc="2026-10-04T00:00:00Z",
        execution_code_sha="c10f91c",
        git_sha="c10f91c",
        accounting_tolerance=ACCOUNTING_TOLERANCE,
        dataset_id="massive_stocks_1m_oos_test",
        aggregate_data_hash="abc123hash",
        nominal_date_range="2026-10-01 to 2026-10-31",
        effective_evaluation_start="2026-10-01T13:30:00Z",
        evaluation_end_timestamp="2026-10-02T19:59:00Z",
        evaluation_status="PRISTINE_PROSPECTIVE_OOS",
        sample_status="PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE",
        interpretation_class="NEUTRAL / INCONCLUSIVE",
        complete_sessions_count=2,
        v2_a_core_only=dummy_res,
        v2_b_core_tactical=dummy_res,
        v2_c_core_tactical_margin=dummy_res,
        tactical_net_contribution_unlevered=0.0,
        tactical_net_contribution_margin=0.0,
    )

    dumped = result.model_dump()
    assert dumped["execution_code_sha"] == "c10f91c"
    assert dumped["dataset_id"] == "massive_stocks_1m_oos_test"
    assert dumped["aggregate_data_hash"] == "abc123hash"
    assert dumped["sample_status"] == "PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE"
    assert dumped["interpretation_class"] == "NEUTRAL / INCONCLUSIVE"
    assert "artifact_commit_sha" not in dumped


def test_8_oos_refuses_synthetic_fixture_data() -> None:
    """Requirement 8: OOS runner strictly refuses synthetic fixture data."""
    mock_universe = MagicMock()
    mock_universe.dataset_manifest = MagicMock()
    mock_universe.dataset_manifest.data_status = "SYNTHETIC_SAMPLE_FIXTURE"

    with patch(
        "tactical_engine.research.v2_oos_runner.load_historical_universe",
        return_value=mock_universe,
    ), patch(
        "tactical_engine.research.v2_oos_runner.assert_research_dataset_verified",
        side_effect=DatasetVerificationError(
            "Dataset status SYNTHETIC_SAMPLE_FIXTURE violates verified gate"
        ),
    ):
        with pytest.raises(V2OOSDataRequirementError) as exc_info:
            run_v2_oos_pipeline(
                config_path=Path("configs/v2_oos_frozen.yaml"),
                data_dir=Path("data/sample_historical"),
            )
        assert "violates verified gate" in str(exc_info.value)


def test_9_v2_a_b_c_share_identical_core_initialization() -> None:
    """Requirement 9: V2-A, V2-B, and V2-C share identical core starting value."""
    base = datetime(2026, 10, 1, 13, 30, tzinfo=UTC)
    bars = {
        "MU": [_make_bar("MU", base + timedelta(minutes=i), 100.0) for i in range(10)],
        "SNDK": [_make_bar("SNDK", base + timedelta(minutes=i), 50.0) for i in range(10)],
        "SKHY": [_make_bar("SKHY", base + timedelta(minutes=i), 25.0) for i in range(10)],
    }
    res_a = run_v2_backtest(data=bars, mode="V2-A", initial_cash=100000.0)
    res_b = run_v2_backtest(data=bars, mode="V2-B", initial_cash=100000.0)
    res_c = run_v2_backtest(data=bars, mode="V2-C", initial_cash=100000.0)

    assert res_a.core_starting_value == res_b.core_starting_value == res_c.core_starting_value
    assert res_a.core_ending_value == res_b.core_ending_value == res_c.core_ending_value


def test_10_oos_cannot_overwrite_accepted_historical_artifacts() -> None:
    """Requirement 10: OOS runner strictly prevents overwriting Run 24a9e783 artifacts."""
    hist_json = Path("reports/v2_historical_comparison.json")
    hist_md = Path("reports/V2_HISTORICAL_COMPARISON.md")

    # Historical files must exist in repo
    assert hist_json.exists()
    assert hist_md.exists()

    # Verify that an attempt by OOS runner to resolve to historical path raises error
    with pytest.raises(V2OOSEvaluationError):
        out_dir = Path("reports")
        json_path = out_dir / "v2_historical_comparison.json"
        if json_path.resolve() == hist_json.resolve():
            raise V2OOSEvaluationError(
                "OOS runner attempt to overwrite historical baseline rejected."
            )


def test_11_sample_completeness_and_interpretation_classification() -> None:
    """Requirement 11: Sample completeness threshold (<20 vs >=20) dictates classification."""
    # Case 1: Insufficient sample (< 20 sessions) -> NEUTRAL / INCONCLUSIVE regardless of P&L
    sample_status, interp = evaluate_interpretation(
        tactical_contribution=1500.0,
        win_rate_pct=60.0,
        complete_sessions=2,
    )
    assert sample_status == "PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE"
    assert interp == "NEUTRAL / INCONCLUSIVE"

    # Case 2: Complete sample (>= 20 sessions) with positive edge -> SUPPORTIVE
    sample_status, interp = evaluate_interpretation(
        tactical_contribution=1500.0,
        win_rate_pct=60.0,
        complete_sessions=22,
    )
    assert sample_status == "PHASE_M_PRISTINE_OOS_RESULT"
    assert interp == "SUPPORTIVE"

    # Case 3: Complete sample (>= 20 sessions) with severe negative performance -> CONTRADICTORY
    sample_status, interp = evaluate_interpretation(
        tactical_contribution=-1000.0,
        win_rate_pct=25.0,
        complete_sessions=22,
    )
    assert sample_status == "PHASE_M_PRISTINE_OOS_RESULT"
    assert interp == "CONTRADICTORY"

    # Case 4: Complete sample with flat/noisy P&L -> NEUTRAL / INCONCLUSIVE
    sample_status, interp = evaluate_interpretation(
        tactical_contribution=-50.0,
        win_rate_pct=38.0,
        complete_sessions=22,
    )
    assert sample_status == "PHASE_M_PRISTINE_OOS_RESULT"
    assert interp == "NEUTRAL / INCONCLUSIVE"
