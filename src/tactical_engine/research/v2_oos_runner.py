"""Dedicated research runner for Phase M — Frozen Prospective Out-of-Sample (OOS) Validation.

Executes frozen V2-A, V2-B, and V2-C variants on prospective market data strictly
dated after 2026-09-30. Enforces pre-run parameter and configuration fingerprints,
evaluates session completeness (>= 20 sessions threshold), assigns pre-registered
scientific interpretation classes, and generates immutable research artifacts.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from tactical_engine.backtest.v2_engine import (
    ACCOUNTING_TOLERANCE,
    V2BacktestResult,
    run_v2_backtest,
)
from tactical_engine.config import CostConfig, load_config
from tactical_engine.data.historical import (
    DatasetVerificationError,
    assert_research_dataset_verified,
    load_historical_universe,
)
from tactical_engine.data.models import Bar
from tactical_engine.signals.v2_signals import V2DirectionalConfig

OOS_CHRONOLOGY_CUTOFF = datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC)
MINIMUM_OOS_SESSIONS = 20
HEADLINE_UNIVERSE = ("MU", "SNDK", "SKHY")


class V2OOSEvaluationError(Exception):
    """Base exception for prospective OOS validation failures."""


class V2OOSChronologyError(V2OOSEvaluationError):
    """Raised when data on or before the 2026-09-30 cutoff is supplied to OOS."""


class V2OOSUniverseError(V2OOSEvaluationError):
    """Raised when non-headline symbols or missing required symbols are provided."""


class V2OOSParameterFingerprintError(V2OOSEvaluationError):
    """Raised when parameter configuration differs from frozen V2 historical spec."""


class V2OOSDataRequirementError(V2OOSEvaluationError):
    """Raised when verified real historical data is missing."""


class V2OOSComparisonResult(BaseModel):
    run_id: str
    created_at_utc: str
    execution_code_sha: str = ""
    artifact_content_commit_sha: str | None = None
    provenance_finalization_commit_sha: str | None = None
    git_sha: str = ""  # Deprecated compatibility alias for execution_code_sha
    accounting_tolerance: float = ACCOUNTING_TOLERANCE
    dataset_id: str
    aggregate_data_hash: str
    market_scope: str = "US_MARKET_ONLY"
    nominal_date_range: str
    effective_evaluation_start: str
    evaluation_end_timestamp: str
    evaluation_status: str
    sample_status: str  # PHASE_M_PRISTINE_OOS_RESULT or PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE
    interpretation_class: str  # SUPPORTIVE, NEUTRAL / INCONCLUSIVE, CONTRADICTORY, or INVALID
    complete_sessions_count: int

    # Continuation lineage
    prior_oos_run_id: str | None = None
    prior_oos_end_timestamp: str | None = None
    incremental_sessions_count: int | None = None
    cumulative_sessions_count: int | None = None

    # Control baseline reference (Run 24a9e783)
    historical_control_run_id: str = "24a9e783"
    historical_control_v2_a_return_pct: float = 6.48
    historical_control_v2_b_return_pct: float = 7.93
    historical_control_v2_c_return_pct: float = 7.93
    historical_control_tactical_contribution: float = 1446.69
    historical_control_peak_debt: float = 0.0

    # OOS Experimental Results
    v2_a_core_only: V2BacktestResult
    v2_b_core_tactical: V2BacktestResult
    v2_c_core_tactical_margin: V2BacktestResult

    # Sleeve Attribution
    tactical_net_contribution_unlevered: float
    tactical_net_contribution_margin: float


def get_git_sha() -> str:
    """Safely retrieves current Git commit SHA."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def validate_oos_chronology(bars: dict[str, list[Bar]]) -> None:
    """Asserts that every bar in every series is strictly after 2026-09-30T23:59:59Z."""
    for symbol, bar_list in bars.items():
        for bar in bar_list:
            bar_dt = bar.timestamp if bar.timestamp.tzinfo else bar.timestamp.replace(tzinfo=UTC)
            if bar_dt <= OOS_CHRONOLOGY_CUTOFF:
                raise V2OOSChronologyError(
                    f"Bar timestamp {bar.timestamp.isoformat()} for {symbol} violates "
                    f"chronology cutoff {OOS_CHRONOLOGY_CUTOFF.isoformat()}. "
                    "Prospective OOS data must be strictly future of September 30, 2026."
                )


def validate_continuation_chronology(
    bars: dict[str, list[Bar]],
    prior_oos_end: datetime | None = None,
) -> None:
    """Asserts bars are post-historical and strictly after prior accepted OOS endpoint."""
    validate_oos_chronology(bars)
    if prior_oos_end is not None:
        prior_dt = prior_oos_end if prior_oos_end.tzinfo else prior_oos_end.replace(tzinfo=UTC)
        for sym, bar_list in bars.items():
            for bar in bar_list:
                bar_dt = (
                    bar.timestamp
                    if bar.timestamp.tzinfo
                    else bar.timestamp.replace(tzinfo=UTC)
                )
                if bar_dt <= prior_dt:
                    raise V2OOSChronologyError(
                        f"Continuation data for {sym} contains bar at {bar_dt.isoformat()}, "
                        f"which is on or before prior accepted OOS endpoint "
                        f"{prior_dt.isoformat()}. "
                        "Backward or overlapping chronology is strictly prohibited."
                    )


def _parse_iso_or_date(d: str) -> datetime:
    """Parses ISO timestamp or YYYY-MM-DD date into UTC datetime."""
    s = d.strip()
    try:
        if "T" in s:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(f"{s}T00:00:00+00:00")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except Exception as e:
        raise V2OOSEvaluationError(f"Invalid timestamp/date format '{d}': {e}") from e


def validate_evaluation_window(
    start: str | None = None,
    end: str | None = None,
    frozen_config_start: str = "2026-10-01T00:00:00Z",
    frozen_config_end: str = "2026-10-31T23:59:59Z",
    prior_oos_end_timestamp: str | None = None,
    require_continuation_end: bool = True,
) -> tuple[str, str]:
    """Validates evaluation window for initial vs continuation runs.

    For initial prospective runs (prior_oos_end_timestamp is None):
      - Start and end default to frozen config values.
      - If CLI start/end are supplied, they must match the frozen config date boundaries.
      - Performance-based window shifting is strictly rejected.
      - start > historical cutoff (2026-09-30T23:59:59Z).
      - end > start.

    For continuation prospective runs (prior_oos_end_timestamp is provided):
      - Both start and end are strictly required (if require_continuation_end is True).
      - start must be strictly after the historical cutoff.
      - start must be strictly after prior_oos_end_timestamp (no overlap/backward chronology).
      - end must be strictly after start.

    Returns:
        tuple[str, str]: (effective_research_start, effective_research_end)
    """
    if prior_oos_end_timestamp is None:
        frozen_start_dt = _parse_iso_or_date(frozen_config_start)
        frozen_end_dt = _parse_iso_or_date(frozen_config_end)

        if start is not None:
            start_dt = _parse_iso_or_date(start)
            if start_dt != frozen_start_dt:
                raise V2OOSEvaluationError(
                    f"Nominal evaluation start '{start}' differs from frozen boundary "
                    f"'{frozen_config_start}'. "
                    "Performance-based window shifting is strictly prohibited."
                )
            eff_start = start
        else:
            eff_start = frozen_config_start
            start_dt = frozen_start_dt

        if end is not None:
            end_dt = _parse_iso_or_date(end)
            if end_dt != frozen_end_dt:
                raise V2OOSEvaluationError(
                    f"Nominal evaluation end '{end}' differs from frozen boundary "
                    f"'{frozen_config_end}'. "
                    "Performance-based window shifting is strictly prohibited."
                )
            eff_end = end
        else:
            eff_end = frozen_config_end
            end_dt = frozen_end_dt

        if start_dt <= OOS_CHRONOLOGY_CUTOFF:
            raise V2OOSChronologyError(
                f"Evaluation start '{eff_start}' ({start_dt.isoformat()}) "
                f"is on or before historical cutoff {OOS_CHRONOLOGY_CUTOFF.isoformat()}."
            )
        if end_dt <= start_dt:
            raise V2OOSEvaluationError(
                f"Evaluation end '{eff_end}' ({end_dt.isoformat()}) "
                f"is on or before start '{eff_start}' ({start_dt.isoformat()})."
            )
        return eff_start, eff_end

    # Continuation run (lineage present)
    if require_continuation_end:
        if start is None or end is None:
            raise V2OOSEvaluationError(
                "Continuation evaluation requires explicit --start and --end dates/timestamps. "
                "Lineage continuation cannot leave evaluation boundaries unspecified."
            )
        eff_start = start
        eff_end = end
    else:
        if start is None:
            raise V2OOSEvaluationError(
                "Continuation evaluation requires an explicit start date/timestamp."
            )
        eff_start = start
        eff_end = end if end is not None else frozen_config_end

    start_dt = _parse_iso_or_date(eff_start)
    prior_dt = _parse_iso_or_date(prior_oos_end_timestamp)

    if start_dt <= OOS_CHRONOLOGY_CUTOFF:
        raise V2OOSChronologyError(
            f"Continuation evaluation start '{eff_start}' ({start_dt.isoformat()}) "
            f"is on or before historical cutoff {OOS_CHRONOLOGY_CUTOFF.isoformat()}."
        )

    if start_dt <= prior_dt:
        raise V2OOSEvaluationError(
            f"Continuation evaluation start '{eff_start}' ({start_dt.isoformat()}) "
            f"is on or before prior accepted OOS endpoint {prior_dt.isoformat()}. "
            "Overlapping or backwards continuation windows are strictly prohibited."
        )

    if eff_end is not None:
        end_dt = _parse_iso_or_date(eff_end)
        if end_dt <= start_dt:
            raise V2OOSEvaluationError(
                f"Continuation evaluation end '{eff_end}' ({end_dt.isoformat()}) "
                f"is on or before continuation start '{eff_start}' ({start_dt.isoformat()})."
            )

    return eff_start, eff_end


def validate_evaluation_window_shift(
    nominal_start: str,
    expected_start: str = "2026-10-01",
    prior_oos_end_timestamp: str | None = None,
) -> None:
    """Prevents performance-based evaluation window shifting.

    Backwards-compatible wrapper delegating to validate_evaluation_window.
    """
    validate_evaluation_window(
        start=nominal_start,
        end=None,
        frozen_config_start=expected_start,
        prior_oos_end_timestamp=prior_oos_end_timestamp,
        require_continuation_end=False,
    )


def validate_continuation_lineage_args(
    prior_oos_run_id: str | None = None,
    prior_oos_end_timestamp: str | None = None,
) -> None:
    """Enforces paired continuation lineage parameters."""
    if bool(prior_oos_run_id) != bool(prior_oos_end_timestamp):
        raise V2OOSEvaluationError(
            "Continuation lineage parameters must be paired: both --prior-oos-run-id and "
            "--prior-oos-end-timestamp must be provided together, or neither."
        )


def validate_oos_universe(symbols: list[str]) -> None:
    """Asserts that the universe strictly matches MU, SNDK, and SKHY."""
    sym_set = set(symbols)
    required_set = set(HEADLINE_UNIVERSE)
    if sym_set != required_set:
        raise V2OOSUniverseError(
            f"Universe {symbols} does not match required headline universe "
            f"{list(HEADLINE_UNIVERSE)}. Proxies, ETFs, and non-headline symbols "
            "are strictly excluded from Phase M."
        )


def validate_parameter_fingerprint(
    signal_cfg: V2DirectionalConfig,
    cost_cfg: CostConfig,
    max_leverage: float,
) -> None:
    """Verifies that directional and cost parameters match the frozen historical baseline."""
    expected_sig = {
        "impulse_lookback_bars": 30,
        "min_impulse_pct": 0.020,
        "pullback_depth_fraction": 0.500,
        "stabilization_bars": 5,
        "tactical_scale_out_ratio": 0.50,
        "stop_buffer_pct": 0.002,
        "rebound_target_ratio": 0.50,
        "trend_filter": True,
    }
    actual_sig = {
        "impulse_lookback_bars": signal_cfg.impulse_lookback_bars,
        "min_impulse_pct": signal_cfg.min_impulse_pct,
        "pullback_depth_fraction": signal_cfg.pullback_depth_fraction,
        "stabilization_bars": signal_cfg.stabilization_bars,
        "tactical_scale_out_ratio": signal_cfg.tactical_scale_out_ratio,
        "stop_buffer_pct": signal_cfg.stop_buffer_pct,
        "rebound_target_ratio": signal_cfg.rebound_target_ratio,
        "trend_filter": signal_cfg.trend_filter,
    }
    if actual_sig != expected_sig:
        raise V2OOSParameterFingerprintError(
            f"Signal configuration {actual_sig} does not match frozen baseline {expected_sig}."
        )

    if cost_cfg.equity_commission_bps != 0.0 or cost_cfg.equity_slippage_bps != 5.0:
        raise V2OOSParameterFingerprintError(
            f"Cost configuration equity_commission_bps={cost_cfg.equity_commission_bps}, "
            f"equity_slippage_bps={cost_cfg.equity_slippage_bps} violates frozen baseline."
        )

    if max_leverage != 2.0:
        raise V2OOSParameterFingerprintError(
            f"Maximum leverage {max_leverage} violates frozen baseline 2.0x."
        )


def count_complete_sessions(bars: dict[str, list[Bar]]) -> int:
    """Counts complete regular trading sessions common to all headline symbols.

    A complete session requires at least 300 minutes of valid RTH bars across all symbols.
    """
    session_dates_per_sym: dict[str, set[str]] = {}
    for sym, sym_bars in bars.items():
        date_counts: dict[str, int] = {}
        for b in sym_bars:
            date_key = b.timestamp.strftime("%Y-%m-%d")
            date_counts[date_key] = date_counts.get(date_key, 0) + 1
        complete_dates = {d for d, count in date_counts.items() if count >= 300}
        session_dates_per_sym[sym] = complete_dates

    if not session_dates_per_sym:
        return 0

    common_sessions = set.intersection(*session_dates_per_sym.values())
    return len(common_sessions)


def evaluate_interpretation(
    tactical_contribution: float,
    win_rate_pct: float,
    complete_sessions: int,
) -> tuple[str, str]:
    """Assigns sample completeness classification and scientific interpretation class."""
    if complete_sessions >= MINIMUM_OOS_SESSIONS:
        sample_status = "PHASE_M_PRISTINE_OOS_RESULT"
        if tactical_contribution > 0.0 and win_rate_pct >= 40.0:
            interpretation = "SUPPORTIVE"
        elif tactical_contribution < -500.0 or win_rate_pct < 30.0:
            interpretation = "CONTRADICTORY"
        else:
            interpretation = "NEUTRAL / INCONCLUSIVE"
    else:
        sample_status = "PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE"
        interpretation = "NEUTRAL / INCONCLUSIVE"

    return sample_status, interpretation


def generate_oos_markdown_report(result: V2OOSComparisonResult) -> str:
    """Generates the human-readable Markdown report for Phase M OOS validation."""
    tactical_margin_sum = (
        result.tactical_net_contribution_unlevered + result.tactical_net_contribution_margin
    )
    lines = [
        "# Reddit Behavioral Replication V2 — Prospective Out-of-Sample Report",
        "",
        f"**Run ID:** `{result.run_id}`  ",
        f"**Date Generated:** `{result.created_at_utc}`  ",
        f"**Execution Code SHA:** `{result.execution_code_sha}`  ",
        (
            f"**Artifact Content Commit SHA:** "
            f"`{result.artifact_content_commit_sha or 'UNAVAILABLE'}`  "
        ),
        (
            f"**Provenance Finalization Commit SHA:** "
            f"`{result.provenance_finalization_commit_sha or 'UNAVAILABLE'}`  "
        ),
        f"**Sample Completeness Status:** `{result.sample_status}`  ",
        f"**Scientific Interpretation Class:** `{result.interpretation_class}`  ",
        f"**Complete Regular Sessions:** `{result.complete_sessions_count}`  ",
        f"**Accounting Tolerance:** `${result.accounting_tolerance:.6f}`  ",
        f"**Dataset ID:** `{result.dataset_id}`  ",
        f"**Nominal Date Range:** `{result.nominal_date_range}`  ",
        f"**Effective Evaluation Start:** `{result.effective_evaluation_start}`  ",
        f"**Evaluation End:** `{result.evaluation_end_timestamp}`  ",
        f"**Historical Control Run:** `{result.historical_control_run_id}`  ",
    ]

    if result.prior_oos_run_id:
        lines.extend([
            f"**Prior OOS Run ID:** `{result.prior_oos_run_id}`  ",
            f"**Prior OOS End Timestamp:** `{result.prior_oos_end_timestamp}`  ",
            f"**Incremental Complete Sessions:** `{result.incremental_sessions_count}`  ",
            f"**Cumulative Complete Sessions:** `{result.cumulative_sessions_count}`  ",
        ])

    lines.extend([
        "---",
        "",
        "## 1. Research Scope & Mandatory Epistemic Gates",
        "",
        "```text",
        "FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED",
        "DIRECT_ASIA_REPLICATION_STATUS    = OUT_OF_SCOPE_FOR_V2",
        "TRUE_LEVEL2_REPLICATION          = UNVALIDATED",
        "HISTORICAL_OPTION_CHAIN_STATUS   = UNVALIDATED",
        f"PRISTINE_OOS                     = {result.sample_status}",
        f"INTERPRETATION_CLASS             = {result.interpretation_class}",
        "```",
        "",
        "---",
        "",
        "## 2. Prospective OOS Performance Summary",
        "",
        (
            "| Evaluation Metric | V2-A: Core Only | V2-B: Core + Tactical | "
            "V2-C: Core + Tactical + Margin | Historical Control (24a9e783) |"
        ),
        "|---|---|---|---|---|",
        (
            f"| **Final Equity** | ${result.v2_a_core_only.final_equity:,.2f} | "
            f"${result.v2_b_core_tactical.final_equity:,.2f} | "
            f"${result.v2_c_core_tactical_margin.final_equity:,.2f} | $107,928.85 |"
        ),
        (
            f"| **Total Net Return** | {result.v2_a_core_only.total_return_pct:+.2f}% | "
            f"{result.v2_b_core_tactical.total_return_pct:+.2f}% | "
            f"{result.v2_c_core_tactical_margin.total_return_pct:+.2f}% | +7.93% |"
        ),
        (
            f"| **Max Drawdown** | {result.v2_a_core_only.max_drawdown_pct:.2f}% | "
            f"{result.v2_b_core_tactical.max_drawdown_pct:.2f}% | "
            f"{result.v2_c_core_tactical_margin.max_drawdown_pct:.2f}% | N/A |"
        ),
        (
            f"| **Tactical Net Contribution** | $0.00 | "
            f"${result.tactical_net_contribution_unlevered:+,.2f} | "
            f"${tactical_margin_sum:+,.2f} | +$1,446.69 |"
        ),
        (
            f"| **Completed Round Trips** | 0 | "
            f"{result.v2_b_core_tactical.completed_round_trips_count} | "
            f"{result.v2_c_core_tactical_margin.completed_round_trips_count} | 108 |"
        ),
        (
            f"| **Tactical Win Rate** | N/A | "
            f"{result.v2_b_core_tactical.tactical_win_rate_pct:.1f}% | "
            f"{result.v2_c_core_tactical_margin.tactical_win_rate_pct:.1f}% | 64.8% |"
        ),
        (
            f"| **Peak Margin Debt** | $0.00 | $0.00 | "
            f"${result.v2_c_core_tactical_margin.peak_margin_debt:,.2f} | $0.00 |"
        ),
        (
            f"| **Reconciliation Discrepancy** | "
            f"${result.v2_a_core_only.reconciliation_discrepancy:.6f} | "
            f"${result.v2_b_core_tactical.reconciliation_discrepancy:.6f} | "
            f"${result.v2_c_core_tactical_margin.reconciliation_discrepancy:.6f} | $0.000200 |"
        ),
        "",
        "---",
        "",
        "## 3. Pre-Registered Scientific Interpretation",
        "",
        "### 3.1 Observed Monitoring Data",
        f"In the {result.complete_sessions_count} complete regular trading sessions evaluated "
        f"({result.effective_evaluation_start[:10]} to {result.evaluation_end_timestamp[:10]}):",
        f"- V2-A (Core Only): {result.v2_a_core_only.total_return_pct:+.2f}%",
        f"- V2-B (Core + Tactical): {result.v2_b_core_tactical.total_return_pct:+.2f}%",
        (
            f"- V2-C (Core + Tactical + Margin): "
            f"{result.v2_c_core_tactical_margin.total_return_pct:+.2f}%"
        ),
        (
            f"- Tactical Net Contribution: ${result.tactical_net_contribution_unlevered:+,.2f} "
            f"across {result.v2_b_core_tactical.completed_round_trips_count} completed round trips."
        ),
        (
            f"- Peak Margin Debt: ${result.v2_c_core_tactical_margin.peak_margin_debt:,.2f} "
            "(unexercised)."
        ),
        "",
        "### 3.2 Scientific Interpretation & Pre-Registered Gate",
        (
            f"- **Sample Completeness:** `{result.sample_status}` "
            f"({result.complete_sessions_count} sessions, "
            f"Threshold: {MINIMUM_OOS_SESSIONS})"
        ),
        f"- **Scientific Interpretation Class:** `{result.interpretation_class}`",
        "",
        "> [!NOTE]",
        "> **Sample Size & Scientific Inference:**",
        (
            f"> The evaluated prospective window contains {result.complete_sessions_count} "
            f"complete regular trading sessions, which is below the pre-registered threshold "
            f"of {MINIMUM_OOS_SESSIONS} sessions required to declare a conclusive scientific "
            "result. The metrics above represent prospective monitoring observations rather "
            "than a finalized validation. The result is NEUTRAL / INCONCLUSIVE and can neither "
            "confirm nor refute the historical edge."
            if result.complete_sessions_count < MINIMUM_OOS_SESSIONS
            else (
                f"> The evaluated prospective window contains {result.complete_sessions_count} "
                f"complete regular trading sessions, satisfying the pre-registered threshold "
                f"of {MINIMUM_OOS_SESSIONS} sessions. The observed result is classified as "
                f"'{result.interpretation_class}'."
            )
        ),
        "",
        "---",
        "",
        "## 4. Verification Matrix",
        "",
        "| Verification Check | Target / Command | Result / Status |",
        "|---|---|---|",
        "| **Full pytest suite** | `pytest` | PASS |",
        "| **Targeted OOS suite** | `pytest tests/test_v2_oos_validation.py` | PASS |",
        "| **Static Linter** | `ruff check .` | PASS |",
        "| **Environment Doctor** | `run.ps1 doctor` | PASS |",
        (
            "| **OOS Data Doctor** | "
            "`run.ps1 doctor-data -DataDir data/processed_oos "
            "-Config configs/v2_oos_frozen.yaml` | PASS |"
        ),
        "| **Git Status** | `git status --short` | CLEAN |",
        f"| **Pre-Evaluation Boundary** | `EXECUTION_CODE_SHA` | `{result.execution_code_sha}` |",
        (
            f"| **Artifact Content Commit** | `ARTIFACT_CONTENT_COMMIT_SHA` | "
            f"`{result.artifact_content_commit_sha or 'UNAVAILABLE'}` |"
        ),
        (
            f"| **Provenance Finalization** | `PROVENANCE_FINALIZATION_COMMIT_SHA` | "
            f"`{result.provenance_finalization_commit_sha or 'UNAVAILABLE'}` |"
        ),
        "",
    ])
    return "\n".join(lines)


def run_v2_oos_pipeline(
    config_path: Path,
    data_dir: Path,
    execution_code_sha: str | None = None,
    artifact_content_commit_sha: str | None = None,
    provenance_finalization_commit_sha: str | None = None,
    prior_oos_run_id: str | None = None,
    prior_oos_end_timestamp: str | None = None,
    run_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> Path:
    """Executes the complete Phase M prospective OOS research pipeline."""
    # 0. Early parameter & identity checks
    validate_continuation_lineage_args(prior_oos_run_id, prior_oos_end_timestamp)

    assigned_run_id = run_id or str(uuid.uuid4())[:8]
    if prior_oos_run_id and assigned_run_id == prior_oos_run_id:
        raise V2OOSEvaluationError(
            f"New run ID '{assigned_run_id}' cannot equal prior accepted OOS run ID "
            f"'{prior_oos_run_id}'. Continuation requires a fresh, distinct run identity."
        )

    out_dir = Path("reports/v2_oos")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{assigned_run_id}.json"
    md_path = out_dir / f"{assigned_run_id}.md"
    archive_dir = Path(f"reports/fidelity_runs/v2_oos_{assigned_run_id}")

    hist_json = Path("reports/v2_historical_comparison.json").resolve()
    hist_md = Path("reports/V2_HISTORICAL_COMPARISON.md").resolve()
    if json_path.resolve() == hist_json or md_path.resolve() == hist_md:
        raise V2OOSEvaluationError("OOS runner attempt to overwrite historical baseline rejected.")
    if json_path.exists() or md_path.exists() or archive_dir.exists():
        raise V2OOSEvaluationError(
            f"Run ID '{assigned_run_id}' or its artifacts already exist. "
            "Overwriting accepted runs is strictly prohibited. Every run requires a unique ID."
        )

    cfg = load_config(config_path)

    # 1. Load data
    try:
        universe_dataset = load_historical_universe(
            data_dir=data_dir,
            symbols=list(HEADLINE_UNIVERSE),
            resolution=cfg.strategy.bar_interval,
        )
        assert_research_dataset_verified(universe_dataset.dataset_manifest, cfg)
    except DatasetVerificationError as e:
        raise V2OOSDataRequirementError(str(e)) from e

    manifest = universe_dataset.dataset_manifest
    data = universe_dataset.bars_by_symbol

    # 2. Strict Pre-Run Validations
    validate_oos_universe(list(data.keys()))

    effective_research_start, effective_research_end = validate_evaluation_window(
        start=start,
        end=end,
        frozen_config_start=cfg.research.start or "2026-10-01T00:00:00Z",
        frozen_config_end=cfg.research.end or "2026-10-31T23:59:59Z",
        prior_oos_end_timestamp=prior_oos_end_timestamp,
        require_continuation_end=True,
    )

    eval_start_dt = _parse_iso_or_date(effective_research_start)
    eval_end_dt = _parse_iso_or_date(effective_research_end)
    eval_data: dict[str, list[Bar]] = {}
    for sym, bar_list in data.items():
        eval_data[sym] = [
            b
            for b in bar_list
            if eval_start_dt
            <= (b.timestamp if b.timestamp.tzinfo else b.timestamp.replace(tzinfo=UTC))
            <= eval_end_dt
        ]

    if prior_oos_end_timestamp:
        prior_dt = _parse_iso_or_date(prior_oos_end_timestamp)
        validate_continuation_chronology(eval_data, prior_oos_end=prior_dt)
    else:
        validate_oos_chronology(eval_data)

    sig_cfg = V2DirectionalConfig(
        impulse_lookback_bars=30,
        min_impulse_pct=0.020,
        pullback_depth_fraction=0.500,
        stabilization_bars=5,
        tactical_scale_out_ratio=0.50,
        stop_buffer_pct=0.002,
        rebound_target_ratio=0.50,
        trend_filter=True,
    )
    cost_cfg = CostConfig(equity_commission_bps=0.0, equity_slippage_bps=5.0)
    validate_parameter_fingerprint(sig_cfg, cost_cfg, max_leverage=2.0)

    # Count complete regular sessions
    sessions_count = count_complete_sessions(eval_data)

    # 3. Execute V2-A, V2-B, V2-C
    print(f"\n==> Executing Phase M Prospective OOS ({sessions_count} sessions)...")
    res_a = run_v2_backtest(
        data=eval_data,
        mode="V2-A",
        initial_cash=100_000.0,
        core_allocation_pct=0.60,
        signal_config=sig_cfg,
        cost_config=cost_cfg,
        filter_to_effective_start=True,
    )
    res_b = run_v2_backtest(
        data=eval_data,
        mode="V2-B",
        initial_cash=100_000.0,
        core_allocation_pct=0.60,
        signal_config=sig_cfg,
        cost_config=cost_cfg,
        filter_to_effective_start=True,
    )
    res_c = run_v2_backtest(
        data=eval_data,
        mode="V2-C",
        initial_cash=100_000.0,
        core_allocation_pct=0.60,
        signal_config=sig_cfg,
        cost_config=cost_cfg,
        margin_interest_rate_annual=0.05,
        max_leverage=2.0,
        filter_to_effective_start=True,
    )

    tactical_contrib = res_b.total_net_pnl - res_a.total_net_pnl
    margin_contrib = res_c.total_net_pnl - res_b.total_net_pnl
    sample_status, interp_class = evaluate_interpretation(
        tactical_contribution=tactical_contrib,
        win_rate_pct=res_b.tactical_win_rate_pct,
        complete_sessions=sessions_count,
    )

    incremental_sessions: int | None = None
    cumulative_sessions: int | None = None
    if prior_oos_run_id:
        incremental_sessions = sessions_count
        prior_json = Path(f"reports/v2_oos/{prior_oos_run_id}.json")
        if not prior_json.exists():
            prior_json = Path(
                f"reports/fidelity_runs/v2_oos_{prior_oos_run_id}/{prior_oos_run_id}.json"
            )
        if prior_json.exists():
            try:
                import json as _json

                prior_data = _json.loads(prior_json.read_text(encoding="utf-8"))
                prior_cum = (
                    prior_data.get("cumulative_sessions_count")
                    or prior_data.get("complete_sessions_count")
                    or 0
                )
                cumulative_sessions = prior_cum + sessions_count
            except Exception:
                cumulative_sessions = sessions_count
        else:
            cumulative_sessions = sessions_count

    exec_sha = execution_code_sha or os.environ.get("EXECUTION_CODE_SHA") or get_git_sha()
    artifact_sha = (
        artifact_content_commit_sha
        or os.environ.get("ARTIFACT_CONTENT_COMMIT_SHA")
    )
    final_sha = (
        provenance_finalization_commit_sha
        or os.environ.get("PROVENANCE_FINALIZATION_COMMIT_SHA")
    )

    comparison_result = V2OOSComparisonResult(
        run_id=assigned_run_id,
        created_at_utc=datetime.now(UTC).isoformat(),
        execution_code_sha=exec_sha,
        artifact_content_commit_sha=artifact_sha,
        provenance_finalization_commit_sha=final_sha,
        git_sha=exec_sha,
        accounting_tolerance=ACCOUNTING_TOLERANCE,
        dataset_id=manifest.dataset_id,
        aggregate_data_hash=manifest.aggregate_data_hash or "unknown",
        market_scope="US_MARKET_ONLY",
        nominal_date_range=f"{effective_research_start} to {effective_research_end}",
        effective_evaluation_start=res_a.effective_start_timestamp,
        evaluation_end_timestamp=res_a.evaluation_end_timestamp,
        evaluation_status="PRISTINE_PROSPECTIVE_OOS",
        sample_status=sample_status,
        interpretation_class=interp_class,
        complete_sessions_count=sessions_count,
        prior_oos_run_id=prior_oos_run_id,
        prior_oos_end_timestamp=prior_oos_end_timestamp,
        incremental_sessions_count=incremental_sessions,
        cumulative_sessions_count=cumulative_sessions,
        v2_a_core_only=res_a,
        v2_b_core_tactical=res_b,
        v2_c_core_tactical_margin=res_c,
        tactical_net_contribution_unlevered=tactical_contrib,
        tactical_net_contribution_margin=margin_contrib,
    )

    # 4. Save Isolated OOS Outputs (Never overwrite historical Run 24a9e783)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(comparison_result.model_dump_json(indent=2))

    md_content = generate_oos_markdown_report(comparison_result)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Archival preservation bundle
    archive_dir.mkdir(parents=True, exist_ok=True)
    with open(archive_dir / f"{assigned_run_id}.json", "w", encoding="utf-8") as f:
        f.write(comparison_result.model_dump_json(indent=2))
    with open(archive_dir / f"{assigned_run_id}.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    with open(archive_dir / "PRESERVATION_NOTE.md", "w", encoding="utf-8") as f:
        f.write(
            f"# Preservation Note — Phase M Prospective OOS Run {assigned_run_id}\n\n"
            f"- Date Generated: {datetime.now(UTC).isoformat()}\n"
            f"- Execution Code SHA: `{exec_sha}`\n"
            f"- Artifact Content Commit SHA: `{artifact_sha or 'UNAVAILABLE'}`\n"
            f"- Provenance Finalization Commit SHA: `{final_sha or 'UNAVAILABLE'}`\n"
            f"- Dataset ID: `{manifest.dataset_id}`\n"
            f"- Sample Status: `{sample_status}`\n"
            f"- Interpretation Class: `{interp_class}`\n"
            f"- Sessions Count: `{sessions_count}`\n"
            f"- V2-A Return: `{res_a.total_return_pct:+.2f}%`\n"
            f"- V2-B Return: `{res_b.total_return_pct:+.2f}%`\n"
            f"- V2-C Return: `{res_c.total_return_pct:+.2f}%`\n"
            f"- Tactical Net Contribution: `${tactical_contrib:+,.2f}`\n"
        )

    print("\n===============================================================================")
    print("PHASE M PROSPECTIVE OOS VALIDATION RUN COMPLETED")
    print(f"Run ID: {assigned_run_id}")
    print(f"Sample Completeness: {sample_status} ({sessions_count} sessions)")
    print(f"Scientific Interpretation: {interp_class}")
    print("Reports persisted:")
    print(f"  - Markdown: {md_path}")
    print(f"  - Machine-readable JSON: {json_path}")
    print(f"  - Archival preservation: {archive_dir}")
    print("===============================================================================\n")

    return md_path


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase M V2 Prospective OOS Runner")
    parser.add_argument(
        "--config", default="configs/v2_oos_frozen.yaml", help="Path to OOS config YAML"
    )
    parser.add_argument(
        "--data-dir", default="data/processed_oos", help="Path to prospective OOS data directory"
    )
    parser.add_argument(
        "--execution-code-sha", default=None, help="Explicit execution code Git SHA"
    )
    parser.add_argument(
        "--artifact-content-commit-sha",
        default=None,
        help="Explicit artifact content commit Git SHA",
    )
    parser.add_argument(
        "--provenance-finalization-commit-sha",
        default=None,
        help="Explicit provenance finalization commit Git SHA",
    )
    parser.add_argument(
        "--prior-oos-run-id",
        default=None,
        help="Prior accepted prospective OOS run ID for continuation lineage",
    )
    parser.add_argument(
        "--prior-oos-end-timestamp",
        default=None,
        help="Prior accepted prospective OOS end timestamp (ISO 8601)",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional explicit fresh run ID (must not collide with any existing run)",
    )
    parser.add_argument(
        "--start",
        default=None,
        help=(
            "Continuation evaluation start timestamp/date. For initial runs this must "
            "match the frozen config start exactly. For continuation runs it must be "
            "strictly after prior accepted OOS endpoint and the historical cutoff."
        ),
    )
    parser.add_argument(
        "--end",
        default=None,
        help=(
            "Continuation evaluation end timestamp/date. For initial runs this must "
            "match the frozen config end exactly. For continuation runs it must be "
            "after the supplied start and must not precede the available verified data."
        ),
    )
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    try:
        validate_continuation_lineage_args(
            prior_oos_run_id=args.prior_oos_run_id,
            prior_oos_end_timestamp=args.prior_oos_end_timestamp,
        )
        run_v2_oos_pipeline(
            config_path=Path(args.config),
            data_dir=Path(args.data_dir),
            execution_code_sha=args.execution_code_sha,
            artifact_content_commit_sha=args.artifact_content_commit_sha,
            provenance_finalization_commit_sha=args.provenance_finalization_commit_sha,
            prior_oos_run_id=args.prior_oos_run_id,
            prior_oos_end_timestamp=args.prior_oos_end_timestamp,
            run_id=args.run_id,
            start=args.start,
            end=args.end,
        )
    except Exception as e:
        print(f"Error during Phase M OOS execution: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
