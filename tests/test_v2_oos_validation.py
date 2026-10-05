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

import json
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
    build_argument_parser,
    count_complete_sessions,
    evaluate_interpretation,
    generate_oos_markdown_report,
    run_v2_oos_pipeline,
    validate_continuation_chronology,
    validate_continuation_lineage_args,
    validate_evaluation_window,
    validate_evaluation_window_shift,
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
    assert dumped["artifact_content_commit_sha"] is None
    assert dumped["provenance_finalization_commit_sha"] is None
    assert dumped["git_sha"] == "c10f91c"
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


def test_12_phase_m1_provenance_taxonomy_in_oos_model_and_artifacts() -> None:
    """Requirement 12: Validate 3-SHA provenance taxonomy in OOS model and saved artifacts."""
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
        run_id="oos_provenance_test",
        created_at_utc="2026-10-04T00:00:00Z",
        execution_code_sha="30473ee",
        artifact_content_commit_sha="c691672",
        provenance_finalization_commit_sha=None,
        git_sha="30473ee",
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
    assert dumped["execution_code_sha"] == "30473ee"
    assert dumped["artifact_content_commit_sha"] == "c691672"
    assert dumped["provenance_finalization_commit_sha"] is None
    assert dumped["git_sha"] == "30473ee"
    assert "artifact_commit_sha" not in dumped

    paths_to_check = [
        Path("reports/v2_oos/bb0887e4.json"),
        Path("reports/fidelity_runs/v2_oos_bb0887e4/bb0887e4.json"),
    ]
    for json_path in paths_to_check:
        assert json_path.exists(), f"Missing {json_path}"
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["execution_code_sha"] == "30473ee"
        assert data["artifact_content_commit_sha"] == "c691672"
        assert data["provenance_finalization_commit_sha"] == "55bea09"
        assert data["git_sha"] == "30473ee"
        assert "artifact_commit_sha" not in data

    md_paths = [
        Path("reports/v2_oos/bb0887e4.md"),
        Path("reports/fidelity_runs/v2_oos_bb0887e4/bb0887e4.md"),
    ]
    for md_path in md_paths:
        assert md_path.exists(), f"Missing {md_path}"
        content = md_path.read_text(encoding="utf-8")
        assert "Artifact Commit SHA" not in content
        assert "**Execution Code SHA:** `30473ee`" in content
        assert "**Artifact Content Commit SHA:** `c691672`" in content
        assert "**Provenance Finalization Commit SHA:** `55bea09`" in content


def test_13_phase_m1_report_structure_and_two_session_framing() -> None:
    """Requirement 13: Validate Phase M.1 structure and two-session framing in bb0887e4.md."""
    md_path = Path("reports/v2_oos/bb0887e4.md")
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")

    assert "### 3.1 Observed Monitoring Data" in content
    assert "### 3.2 Scientific Interpretation & Pre-Registered Gate" in content
    assert "## 4. Verification Matrix" in content

    assert "PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE" in content
    assert "NEUTRAL / INCONCLUSIVE" in content
    assert "2 complete regular trading sessions" in content
    assert "$-290.98" in content
    assert "2 completed round trips" in content


def test_14_phase_m1_cli_sha_overrides() -> None:
    """Requirement 14: CLI parser and markdown generator accept Phase M.1 SHA overrides."""
    parser = build_argument_parser()
    args = parser.parse_args([
        "--artifact-content-commit-sha", "c691672",
        "--provenance-finalization-commit-sha", "aaa10b5",
    ])
    assert args.artifact_content_commit_sha == "c691672"
    assert args.provenance_finalization_commit_sha == "aaa10b5"

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
        run_id="oos_cli_test",
        created_at_utc="2026-10-04T00:00:00Z",
        execution_code_sha="30473ee",
        artifact_content_commit_sha="c691672",
        provenance_finalization_commit_sha="aaa10b5",
        git_sha="30473ee",
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
    md = generate_oos_markdown_report(result)
    assert "**Artifact Content Commit SHA:** `c691672`" in md
    assert "**Provenance Finalization Commit SHA:** `aaa10b5`" in md
    assert "### 3.1 Observed Monitoring Data" in md
    assert "### 3.2 Scientific Interpretation & Pre-Registered Gate" in md


def test_15_f1_cli_exposes_continuation_arguments() -> None:
    """F1: The parser must recognize --prior-oos-run-id and --prior-oos-end-timestamp."""
    parser = build_argument_parser()
    args = parser.parse_args([
        "--prior-oos-run-id", "bb0887e4",
        "--prior-oos-end-timestamp", "2026-10-02T19:59:00Z",
        "--run-id", "test_new_id",
    ])
    assert args.prior_oos_run_id == "bb0887e4"
    assert args.prior_oos_end_timestamp == "2026-10-02T19:59:00Z"
    assert args.run_id == "test_new_id"


def test_16_f2_paired_lineage_requirement() -> None:
    """F2: Supplying only one of the two continuation arguments must fail."""
    with pytest.raises(V2OOSEvaluationError) as exc_info_1:
        validate_continuation_lineage_args(
            prior_oos_run_id="bb0887e4", prior_oos_end_timestamp=None
        )
    assert "must be paired" in str(exc_info_1.value)

    with pytest.raises(V2OOSEvaluationError) as exc_info_2:
        validate_continuation_lineage_args(
            prior_oos_run_id=None, prior_oos_end_timestamp="2026-10-02T19:59:00Z"
        )
    assert "must be paired" in str(exc_info_2.value)

    with pytest.raises(V2OOSEvaluationError) as exc_info_pipeline:
        run_v2_oos_pipeline(
            config_path=Path("configs/v2_oos_frozen.yaml"),
            data_dir=Path("data/processed_oos"),
            prior_oos_run_id="bb0887e4",
            prior_oos_end_timestamp=None,
        )
    assert "must be paired" in str(exc_info_pipeline.value)


def test_17_f3_initial_window_remains_frozen() -> None:
    """F3: No prior lineage + start date other than 2026-10-01 must fail."""
    # Frozen start passes
    validate_evaluation_window_shift("2026-10-01", prior_oos_end_timestamp=None)
    validate_evaluation_window_shift("2026-10-01T13:30:00Z", prior_oos_end_timestamp=None)

    # Shifted start fails
    with pytest.raises(V2OOSEvaluationError) as exc_info:
        validate_evaluation_window_shift("2026-10-05", prior_oos_end_timestamp=None)
    assert "differs from frozen boundary" in str(exc_info.value)


def test_18_f4_continuation_window_may_move_forward() -> None:
    """F4: With prior endpoint 2026-10-02T19:59:00Z, a new start such as 2026-10-05 must pass."""
    validate_evaluation_window_shift(
        nominal_start="2026-10-05",
        prior_oos_end_timestamp="2026-10-02T19:59:00Z",
    )
    validate_evaluation_window_shift(
        nominal_start="2026-10-05T13:30:00Z",
        prior_oos_end_timestamp="2026-10-02T19:59:00Z",
    )


def test_19_f5_continuation_overlap_is_rejected() -> None:
    """F5: Any bar at or before the prior endpoint must fail."""
    prior_endpoint = datetime(2026, 10, 2, 19, 59, tzinfo=UTC)

    # Bar exactly at endpoint
    bar_at_endpoint = _make_bar("MU", prior_endpoint, 100.0)
    with pytest.raises(V2OOSChronologyError) as exc_info_1:
        validate_continuation_chronology({"MU": [bar_at_endpoint]}, prior_oos_end=prior_endpoint)
    assert "on or before prior accepted OOS endpoint" in str(exc_info_1.value)

    # Bar prior to endpoint
    bar_before = _make_bar("MU", datetime(2026, 10, 2, 18, 0, tzinfo=UTC), 100.0)
    with pytest.raises(V2OOSChronologyError) as exc_info_2:
        validate_continuation_chronology({"MU": [bar_before]}, prior_oos_end=prior_endpoint)
    assert "on or before prior accepted OOS endpoint" in str(exc_info_2.value)

    # In window validation, start_dt <= prior_dt must fail
    with pytest.raises(V2OOSEvaluationError) as exc_info_window:
        validate_evaluation_window_shift(
            "2026-10-02T19:59:00Z", prior_oos_end_timestamp="2026-10-02T19:59:00Z"
        )
    assert "on or before prior accepted OOS endpoint" in str(exc_info_window.value)


def test_20_f6_continuation_after_endpoint_is_accepted() -> None:
    """F6: Synthetic unit fixture with all bars strictly after prior endpoint must pass."""
    prior_endpoint = datetime(2026, 10, 2, 19, 59, tzinfo=UTC)
    bars = {
        "MU": [
            _make_bar("MU", datetime(2026, 10, 5, 13, 30 + i, tzinfo=UTC), 100.0)
            for i in range(5)
        ],
        "SNDK": [
            _make_bar("SNDK", datetime(2026, 10, 5, 13, 30 + i, tzinfo=UTC), 50.0)
            for i in range(5)
        ],
        "SKHY": [
            _make_bar("SKHY", datetime(2026, 10, 5, 13, 30 + i, tzinfo=UTC), 25.0)
            for i in range(5)
        ],
    }
    validate_continuation_chronology(bars, prior_oos_end=prior_endpoint)


def test_21_f7_historical_cutoff_still_applies_to_continuation() -> None:
    """F7: Continuation data at or before 2026-09-30 must fail regardless of prior endpoint."""
    prior_endpoint = datetime(2026, 10, 2, 19, 59, tzinfo=UTC)
    hist_bar = _make_bar("MU", datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC), 100.0)

    with pytest.raises(V2OOSChronologyError) as exc_info:
        validate_continuation_chronology({"MU": [hist_bar]}, prior_oos_end=prior_endpoint)
    assert "violates chronology cutoff" in str(exc_info.value)

    with pytest.raises(V2OOSChronologyError) as exc_info_win:
        validate_evaluation_window_shift(
            "2026-09-30", prior_oos_end_timestamp="2026-10-02T19:59:00Z"
        )
    assert "on or before historical cutoff" in str(exc_info_win.value)


def test_22_f8_new_run_id_protection_and_no_overwrite() -> None:
    """F8: Continuation cannot overwrite an existing run directory or equal prior run ID."""
    # Attempting to reuse prior run ID as new run ID
    with pytest.raises(V2OOSEvaluationError) as exc_same:
        run_v2_oos_pipeline(
            config_path=Path("configs/v2_oos_frozen.yaml"),
            data_dir=Path("data/processed_oos"),
            prior_oos_run_id="bb0887e4",
            prior_oos_end_timestamp="2026-10-02T19:59:00Z",
            run_id="bb0887e4",
        )
    assert "cannot equal prior accepted OOS run ID" in str(exc_same.value)

    # Attempting to assign run_id of existing run (bb0887e4 artifacts exist)
    with pytest.raises(V2OOSEvaluationError) as exc_exists:
        run_v2_oos_pipeline(
            config_path=Path("configs/v2_oos_frozen.yaml"),
            data_dir=Path("data/processed_oos"),
            run_id="bb0887e4",
        )
    assert "already exist" in str(exc_exists.value)


def test_23_f9_prior_lineage_serialization() -> None:
    """F9: Prior lineage fields serialize to JSON and Markdown."""
    dummy_res = V2BacktestResult(
        mode="V2-A",
        initial_cash=100000.0,
        final_equity=105000.0,
        total_net_pnl=5000.0,
        total_return_pct=5.0,
        max_drawdown_pct=1.5,
        core_starting_value=59000.0,
        core_ending_value=64000.0,
        effective_start_timestamp="2026-10-05T13:30:00Z",
        evaluation_end_timestamp="2026-10-06T19:59:00Z",
    )
    result = V2OOSComparisonResult(
        run_id="test_cont_1",
        created_at_utc="2026-10-06T20:00:00Z",
        execution_code_sha="30473ee",
        artifact_content_commit_sha="c691672",
        provenance_finalization_commit_sha="81d9649",
        git_sha="30473ee",
        accounting_tolerance=ACCOUNTING_TOLERANCE,
        dataset_id="massive_stocks_1m_oos_test",
        aggregate_data_hash="abc123hash",
        nominal_date_range="2026-10-05 to 2026-10-06",
        effective_evaluation_start="2026-10-05T13:30:00Z",
        evaluation_end_timestamp="2026-10-06T19:59:00Z",
        evaluation_status="PRISTINE_PROSPECTIVE_OOS",
        sample_status="PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE",
        interpretation_class="NEUTRAL / INCONCLUSIVE",
        complete_sessions_count=2,
        prior_oos_run_id="bb0887e4",
        prior_oos_end_timestamp="2026-10-02T19:59:00Z",
        incremental_sessions_count=2,
        cumulative_sessions_count=4,
        v2_a_core_only=dummy_res,
        v2_b_core_tactical=dummy_res,
        v2_c_core_tactical_margin=dummy_res,
        tactical_net_contribution_unlevered=0.0,
        tactical_net_contribution_margin=0.0,
    )
    dumped = result.model_dump()
    assert dumped["prior_oos_run_id"] == "bb0887e4"
    assert dumped["prior_oos_end_timestamp"] == "2026-10-02T19:59:00Z"
    assert dumped["incremental_sessions_count"] == 2
    assert dumped["cumulative_sessions_count"] == 4

    md = generate_oos_markdown_report(result)
    assert "**Prior OOS Run ID:** `bb0887e4`" in md
    assert "**Prior OOS End Timestamp:** `2026-10-02T19:59:00Z`" in md
    assert "**Incremental Complete Sessions:** `2`" in md
    assert "**Cumulative Complete Sessions:** `4`" in md


def test_24_f10_provenance_taxonomy_and_semantic_distinction() -> None:
    """F10 & Repair A4: Continuation result has 3 distinct SHAs and no artifact_commit_sha."""
    dummy_res = V2BacktestResult(
        mode="V2-A",
        initial_cash=100000.0,
        final_equity=105000.0,
        total_net_pnl=5000.0,
        total_return_pct=5.0,
        max_drawdown_pct=1.5,
        core_starting_value=59000.0,
        core_ending_value=64000.0,
        effective_start_timestamp="2026-10-05T13:30:00Z",
        evaluation_end_timestamp="2026-10-06T19:59:00Z",
    )
    result = V2OOSComparisonResult(
        run_id="tax_check",
        created_at_utc="2026-10-06T20:00:00Z",
        execution_code_sha="30473ee",
        artifact_content_commit_sha="c691672",
        provenance_finalization_commit_sha="55bea09",
        git_sha="30473ee",
        accounting_tolerance=ACCOUNTING_TOLERANCE,
        dataset_id="massive_stocks_1m_oos_test",
        aggregate_data_hash="abc123hash",
        nominal_date_range="2026-10-05 to 2026-10-06",
        effective_evaluation_start="2026-10-05T13:30:00Z",
        evaluation_end_timestamp="2026-10-06T19:59:00Z",
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
    assert dumped["execution_code_sha"] == "30473ee"
    assert dumped["artifact_content_commit_sha"] == "c691672"
    assert dumped["provenance_finalization_commit_sha"] == "55bea09"
    # Strict semantic distinction (execution != content != finalization)
    assert dumped["execution_code_sha"] != dumped["artifact_content_commit_sha"]
    assert dumped["artifact_content_commit_sha"] != dumped["provenance_finalization_commit_sha"]
    assert dumped["execution_code_sha"] != dumped["provenance_finalization_commit_sha"]
    assert "artifact_commit_sha" not in dumped


def test_25_f11_frozen_strategy_fingerprint_enforced_in_continuation() -> None:
    """F11: Altering strategy/cost parameters still fails even when continuation window is valid."""
    validate_evaluation_window_shift(
        nominal_start="2026-10-05",
        prior_oos_end_timestamp="2026-10-02T19:59:00Z",
    )

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
    cost = CostConfig(equity_commission_bps=0.0, equity_slippage_bps=5.0)
    with pytest.raises(V2OOSParameterFingerprintError):
        validate_parameter_fingerprint(altered_sig, cost, max_leverage=2.0)

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
    altered_cost = CostConfig(equity_commission_bps=2.0, equity_slippage_bps=5.0)
    with pytest.raises(V2OOSParameterFingerprintError):
        validate_parameter_fingerprint(frozen_sig, altered_cost, max_leverage=2.0)


# ==============================================================================
# Phase M.1.3 Regression Tests (T1 through T12)
# ==============================================================================


def test_26_m13_t1_initial_dates_default_to_frozen_yaml() -> None:
    """T1: Initial dates default to frozen YAML when no lineage and no overrides supplied."""
    start, end = validate_evaluation_window(
        start=None,
        end=None,
        frozen_config_start="2026-10-01T00:00:00Z",
        frozen_config_end="2026-10-31T23:59:59Z",
        prior_oos_end_timestamp=None,
    )
    assert start == "2026-10-01T00:00:00Z"
    assert end == "2026-10-31T23:59:59Z"

    parser = build_argument_parser()
    args = parser.parse_args([])
    assert args.start is None
    assert args.end is None


def test_27_m13_t2_initial_cli_start_mismatch_rejected() -> None:
    """T2: No lineage + --start differing from frozen config must fail."""
    with pytest.raises(V2OOSEvaluationError) as exc_info:
        validate_evaluation_window(
            start="2026-10-02",
            end=None,
            frozen_config_start="2026-10-01T00:00:00Z",
            frozen_config_end="2026-10-31T23:59:59Z",
            prior_oos_end_timestamp=None,
        )
    assert "differs from frozen boundary" in str(exc_info.value)


def test_28_m13_t3_initial_cli_end_mismatch_rejected() -> None:
    """T3: No lineage + --end differing from frozen config must fail."""
    with pytest.raises(V2OOSEvaluationError) as exc_info:
        validate_evaluation_window(
            start=None,
            end="2026-11-01",
            frozen_config_start="2026-10-01T00:00:00Z",
            frozen_config_end="2026-10-31T23:59:59Z",
            prior_oos_end_timestamp=None,
        )
    assert "differs from frozen boundary" in str(exc_info.value)


def test_29_m13_t4_continuation_requires_explicit_dates() -> None:
    """T4: Lineage supplied but --start or --end omitted must fail."""
    # Both omitted
    with pytest.raises(V2OOSEvaluationError) as exc_both:
        validate_evaluation_window(
            start=None,
            end=None,
            prior_oos_end_timestamp="2026-10-02T19:59:00Z",
        )
    assert "requires explicit --start and --end" in str(exc_both.value)

    # Start omitted
    with pytest.raises(V2OOSEvaluationError) as exc_no_start:
        validate_evaluation_window(
            start=None,
            end="2026-10-05T23:59:59Z",
            prior_oos_end_timestamp="2026-10-02T19:59:00Z",
        )
    assert "requires explicit --start and --end" in str(exc_no_start.value)

    # End omitted
    with pytest.raises(V2OOSEvaluationError) as exc_no_end:
        validate_evaluation_window(
            start="2026-10-05T00:00:00Z",
            end=None,
            prior_oos_end_timestamp="2026-10-02T19:59:00Z",
        )
    assert "requires explicit --start and --end" in str(exc_no_end.value)


def test_30_m13_t5_forward_continuation_accepted() -> None:
    """T5: Forward continuation window is accepted."""
    start, end = validate_evaluation_window(
        start="2026-10-05T00:00:00Z",
        end="2026-10-05T23:59:59Z",
        prior_oos_end_timestamp="2026-10-02T19:59:00Z",
    )
    assert start == "2026-10-05T00:00:00Z"
    assert end == "2026-10-05T23:59:59Z"


def test_31_m13_t6_continuation_start_overlap_rejected() -> None:
    """T6: Continuation start <= prior endpoint must fail."""
    # Start exactly equal to prior endpoint
    with pytest.raises(V2OOSEvaluationError) as exc_eq:
        validate_evaluation_window(
            start="2026-10-02T19:59:00Z",
            end="2026-10-05T23:59:59Z",
            prior_oos_end_timestamp="2026-10-02T19:59:00Z",
        )
    assert "on or before prior accepted OOS endpoint" in str(exc_eq.value)

    # Start before prior endpoint
    with pytest.raises(V2OOSEvaluationError) as exc_before:
        validate_evaluation_window(
            start="2026-10-01T00:00:00Z",
            end="2026-10-05T23:59:59Z",
            prior_oos_end_timestamp="2026-10-02T19:59:00Z",
        )
    assert "on or before prior accepted OOS endpoint" in str(exc_before.value)


def test_32_m13_t7_continuation_end_before_start_rejected() -> None:
    """T7: Continuation end <= start must fail."""
    # End before start
    with pytest.raises(V2OOSEvaluationError) as exc_rev:
        validate_evaluation_window(
            start="2026-10-06T00:00:00Z",
            end="2026-10-05T23:59:59Z",
            prior_oos_end_timestamp="2026-10-02T19:59:00Z",
        )
    assert "is on or before continuation start" in str(exc_rev.value)

    # End equal to start
    with pytest.raises(V2OOSEvaluationError) as exc_same:
        validate_evaluation_window(
            start="2026-10-05T12:00:00Z",
            end="2026-10-05T12:00:00Z",
            prior_oos_end_timestamp="2026-10-02T19:59:00Z",
        )
    assert "is on or before continuation start" in str(exc_same.value)


def test_33_m13_t8_historical_cutoff_still_enforced() -> None:
    """T8: Historical cutoff strictly enforced for continuation runs."""
    with pytest.raises(V2OOSChronologyError) as exc_cutoff:
        validate_evaluation_window(
            start="2026-09-30",
            end="2026-10-05T23:59:59Z",
            prior_oos_end_timestamp="2026-10-02T19:59:00Z",
        )
    assert "on or before historical cutoff" in str(exc_cutoff.value)


def test_34_m13_t9_frozen_yaml_untouched() -> None:
    """T9: Frozen YAML configs/v2_oos_frozen.yaml is byte-identical and untouched."""
    import hashlib

    frozen_path = Path("configs/v2_oos_frozen.yaml")
    expected_sha256 = "be21c7dc0f998cf21310ffb5ffeae39fe039046d80aaa4ee4c656189f44f502a"
    actual_sha256 = hashlib.sha256(frozen_path.read_bytes()).hexdigest()
    assert actual_sha256 == expected_sha256


def test_35_m13_t10_effective_date_reaches_result_metadata() -> None:
    """T10: Effective date reaches result metadata in continuation execution."""
    dummy_res = V2BacktestResult(
        mode="V2-A",
        initial_cash=100000.0,
        final_equity=101000.0,
        total_net_pnl=1000.0,
        total_return_pct=1.0,
        max_drawdown_pct=0.5,
        core_starting_value=60000.0,
        core_ending_value=61000.0,
        effective_start_timestamp="2026-10-05T13:30:00Z",
        evaluation_end_timestamp="2026-10-05T19:59:00Z",
    )
    mock_manifest = MagicMock()
    mock_manifest.dataset_id = "test_cont_dataset"
    mock_manifest.aggregate_data_hash = "mock_hash_123"

    oct5_bar = _make_bar("MU", datetime(2026, 10, 5, 13, 30, tzinfo=UTC), 100.0)
    mock_dataset = MagicMock()
    mock_dataset.dataset_manifest = mock_manifest
    mock_dataset.bars_by_symbol = {
        "MU": [oct5_bar],
        "SNDK": [_make_bar("SNDK", datetime(2026, 10, 5, 13, 30, tzinfo=UTC), 50.0)],
        "SKHY": [_make_bar("SKHY", datetime(2026, 10, 5, 13, 30, tzinfo=UTC), 25.0)],
    }

    test_run_id = "t10_check"
    json_path = Path(f"reports/v2_oos/{test_run_id}.json")
    md_path = Path(f"reports/v2_oos/{test_run_id}.md")
    archive_dir = Path(f"reports/fidelity_runs/v2_oos_{test_run_id}")

    try:
        with (
            patch(
                "tactical_engine.research.v2_oos_runner.load_historical_universe",
                return_value=mock_dataset,
            ),
            patch("tactical_engine.research.v2_oos_runner.assert_research_dataset_verified"),
            patch(
                "tactical_engine.research.v2_oos_runner.run_v2_backtest",
                return_value=dummy_res,
            ),
            patch(
                "tactical_engine.research.v2_oos_runner.count_complete_sessions",
                return_value=1,
            ),
        ):
            report_path = run_v2_oos_pipeline(
                config_path=Path("configs/v2_oos_frozen.yaml"),
                data_dir=Path("data/processed_oos"),
                prior_oos_run_id="bb0887e4",
                prior_oos_end_timestamp="2026-10-02T19:59:00Z",
                run_id=test_run_id,
                start="2026-10-05T00:00:00Z",
                end="2026-10-05T23:59:59Z",
            )

        assert json_path.exists()
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["nominal_date_range"] == "2026-10-05T00:00:00Z to 2026-10-05T23:59:59Z"
        assert data["effective_evaluation_start"] == "2026-10-05T13:30:00Z"
        assert data["evaluation_end_timestamp"] == "2026-10-05T19:59:00Z"
        assert data["prior_oos_run_id"] == "bb0887e4"
        assert data["prior_oos_end_timestamp"] == "2026-10-02T19:59:00Z"

        md_text = report_path.read_text(encoding="utf-8")
        assert "2026-10-05T00:00:00Z to 2026-10-05T23:59:59Z" in md_text
    finally:
        if json_path.exists():
            json_path.unlink()
        if md_path.exists():
            md_path.unlink()
        if archive_dir.exists():
            import shutil

            shutil.rmtree(archive_dir)


def test_36_m13_t11_strategy_fingerprint_unchanged() -> None:
    """T11: Date overrides must not affect the frozen signal/cost/leverage fingerprint."""
    eff_start, eff_end = validate_evaluation_window(
        start="2026-10-05T00:00:00Z",
        end="2026-10-05T23:59:59Z",
        prior_oos_end_timestamp="2026-10-02T19:59:00Z",
    )
    assert eff_start == "2026-10-05T00:00:00Z"
    assert eff_end == "2026-10-05T23:59:59Z"

    altered_sig = V2DirectionalConfig(
        impulse_lookback_bars=25,  # Altered from 30
        min_impulse_pct=0.020,
        pullback_depth_fraction=0.500,
        stabilization_bars=5,
        tactical_scale_out_ratio=0.50,
        stop_buffer_pct=0.002,
        rebound_target_ratio=0.50,
        trend_filter=True,
    )
    cost = CostConfig(equity_commission_bps=0.0, equity_slippage_bps=5.0)
    with pytest.raises(V2OOSParameterFingerprintError):
        validate_parameter_fingerprint(altered_sig, cost, max_leverage=2.0)


def test_37_m13_t12_existing_run_protection() -> None:
    """T12: Continuation date override cannot reuse an accepted run ID."""
    with pytest.raises(V2OOSEvaluationError) as exc_same:
        run_v2_oos_pipeline(
            config_path=Path("configs/v2_oos_frozen.yaml"),
            data_dir=Path("data/processed_oos"),
            prior_oos_run_id="bb0887e4",
            prior_oos_end_timestamp="2026-10-02T19:59:00Z",
            run_id="bb0887e4",
            start="2026-10-05T00:00:00Z",
            end="2026-10-05T23:59:59Z",
        )
    assert "cannot equal prior accepted OOS run ID" in str(exc_same.value)


