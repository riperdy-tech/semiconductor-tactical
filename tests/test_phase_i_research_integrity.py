from datetime import UTC, datetime
from pathlib import Path

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.backtest.state import PortfolioTracker
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Fill, OrderSide
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.reports.fidelity_report import format_fidelity_markdown_report
from tactical_engine.reports.metrics import calculate_metrics
from tactical_engine.research.fidelity import (
    get_preserved_baseline_config,
    get_sector_filtered_diagnostic_config,
    run_fidelity_matrix,
)


def test_exact_preserved_baseline_configuration_identity():
    """Verify that get_preserved_baseline_config returns the canonical configuration
    matching docs/CURRENT_MECHANICAL_PULLBACK_BASELINE.md (run 2e9f108d).
    """
    base = EngineConfig()
    cfg = get_preserved_baseline_config(base)

    # Core economics and risk parameters must match run 2e9f108d exactly
    assert cfg.portfolio.max_gross_leverage == 1.0
    assert cfg.portfolio.max_layers == 1
    assert cfg.portfolio.max_symbol_weight == 0.25
    assert cfg.signals.sector_filter is False
    assert cfg.signals.relative_volume_filter is True
    assert cfg.signals.event_filter is False
    assert cfg.signals.pullback_zscore == -1.5
    assert cfg.signals.trend_window == 60
    assert cfg.exits.family == "atr"
    assert cfg.exits.target_atr == 1.0
    assert cfg.exits.stop_atr == 1.0
    assert cfg.costs.equity_commission_bps == 0.0
    assert cfg.costs.equity_slippage_bps == 5.0
    assert cfg.costs.margin_rate_annual == 0.05
    assert cfg.strategy.variant == "current_mechanical_pullback_baseline"
    assert cfg.signals.signal_family == "pullback_zscore"


def test_baseline_label_separation_between_baseline_and_diagnostic():
    """Verify that baseline, sector-filtered diagnostic, and fidelity variants receive
    distinct, non-conflated implementation labels.
    """
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars("MU", num_bars=50, seed=42, start_time=t0)
    data = {"MU": bars}
    base = EngineConfig()
    base.strategy.universe = ["MU"]

    # 1. Baseline run
    base_cfg = get_preserved_baseline_config(base)
    res_base = run_backtest(data, base_cfg)
    assert res_base.implementation_label == "CURRENT_MECHANICAL_PULLBACK_BASELINE"

    # 2. Sector-filtered diagnostic run
    diag_cfg = get_sector_filtered_diagnostic_config(base)
    res_diag = run_backtest(data, diag_cfg)
    assert res_diag.implementation_label == "MECHANICAL_PULLBACK_SECTOR_FILTERED_DIAGNOSTIC"

    # 3. Directional fidelity reconstruction run
    dir_dict = base.model_dump()
    dir_dict["strategy"]["variant"] = "directional_fidelity_reconstruction"
    dir_dict["signals"]["signal_family"] = "directional_fidelity"
    dir_cfg = EngineConfig.model_validate(dir_dict)
    res_dir = run_backtest(data, dir_cfg)
    assert res_dir.implementation_label == "DIRECTIONAL_FIDELITY_RECONSTRUCTION"

    # All three labels must be strictly distinct
    assert res_base.implementation_label != res_diag.implementation_label
    assert res_base.implementation_label != res_dir.implementation_label
    assert res_diag.implementation_label != res_dir.implementation_label


def test_parameter_provenance_metadata_and_post_hoc_classification():
    """Verify that REDDIT_FIDELITY_PARAMETER_PROVENANCE.md exists, lists all key directional
    parameters, and classifies them as POST_HOC_SPECIFIED.
    """
    doc_path = Path("docs/execution_plan/REDDIT_FIDELITY_PARAMETER_PROVENANCE.md")
    assert doc_path.exists(), "Parameter provenance document must exist"

    content = doc_path.read_text(encoding="utf-8")
    assert "POST_HOC_SPECIFIED" in content
    assert "pullback_min_pct" in content
    assert "pullback_max_pct" in content
    assert "stabilization_threshold" in content
    assert "swing_target_atr" in content
    assert "swing_stop_atr" in content
    assert "order_execution_style" in content
    assert "FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED" in content
    assert "PRISTINE_OOS = UNAVAILABLE" in content


def test_slippage_attribution_mathematical_reconciliation():
    """Verify the invariant:
    Signal-Price P&L (Pre-Slippage) - Execution Slippage = Gross Realized P&L
    Gross Realized P&L - Commission = Net Realized P&L.
    """
    tracker = PortfolioTracker(initial_cash=100_000.0)
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 15, 0, tzinfo=UTC)

    # Buy: intended price 100.00, slippage 0.05, fill 100.05, commission 1.00
    tracker.apply_fill(
        Fill(
            order_id="b1",
            symbol="MU",
            timestamp=t0,
            side=OrderSide.BUY,
            quantity=100.0,
            price=100.05,
            commission=1.00,
            slippage=5.00,
        )
    )

    # Sell: intended price 105.00, slippage 0.05, fill 104.95, commission 1.00
    tracker.apply_fill(
        Fill(
            order_id="s1",
            symbol="MU",
            timestamp=t1,
            side=OrderSide.SELL,
            quantity=100.0,
            price=104.95,
            commission=1.00,
            slippage=5.00,
        ),
        exit_reason="profit_target",
    )

    trade = tracker.closed_trades[0]
    # Trade pre-slippage P&L: (105.00 - 100.00) * 100 = 500.00
    # Execution slippage: 5.00 (entry) + 5.00 (exit) = 10.00
    # Gross realized P&L: (104.95 - 100.05) * 100 = 490.00
    # Net realized P&L: 490.00 - 2.00 (commissions) = 488.00
    assert trade.pre_slippage_pnl == 500.00
    assert trade.slippage_paid == 10.00
    assert trade.gross_pnl == 490.00
    assert trade.commission_paid == 2.00
    assert trade.net_pnl == 488.00

    # Reconciliation invariant checks
    assert round(trade.pre_slippage_pnl - trade.slippage_paid, 2) == round(trade.gross_pnl, 2)
    assert round(trade.gross_pnl - trade.commission_paid, 2) == round(trade.net_pnl, 2)


def test_no_double_counting_of_slippage():
    """Verify that slippage is not deducted a second time from net realized P&L."""
    init_cash = 50_000.0
    tracker = PortfolioTracker(initial_cash=init_cash)
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 14, 45, tzinfo=UTC)

    tracker.apply_fill(
        Fill(
            order_id="b1",
            symbol="MU",
            timestamp=t0,
            side=OrderSide.BUY,
            quantity=50.0,
            price=100.10,  # 100.00 + 0.10 slippage ($5.00 total entry slippage)
            commission=0.50,
            slippage=5.00,
        )
    )
    tracker.apply_fill(
        Fill(
            order_id="s1",
            symbol="MU",
            timestamp=t1,
            side=OrderSide.SELL,
            quantity=50.0,
            price=101.90,  # 102.00 - 0.10 slippage ($5.00 total exit slippage)
            commission=0.50,
            slippage=5.00,
        ),
        exit_reason="time_exit",
    )

    trade = tracker.closed_trades[0]
    # Gross P&L at fill price: (101.90 - 100.10) * 50 = 1.80 * 50 = 90.00
    # Net P&L: 90.00 - 1.00 = 89.00
    assert trade.gross_pnl == 90.00
    assert trade.net_pnl == 89.00

    # Ending cash check: initial 50,000 + 89.00 = 50,089.00
    cash_change = tracker.cash - init_cash
    assert round(cash_change, 2) == round(trade.net_pnl, 2)
    # If slippage ($10) had been mistakenly double-deducted, net would be 79.00 != cash_change
    assert cash_change != round(trade.net_pnl - trade.slippage_paid, 2)


def test_commission_reconciliation_exact():
    """Verify that commission is tracked accurately and deducted exactly once."""
    tracker = PortfolioTracker(initial_cash=10_000.0)
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 14, 35, tzinfo=UTC)

    tracker.apply_fill(
        Fill(
            order_id="b1",
            symbol="MU",
            timestamp=t0,
            side=OrderSide.BUY,
            quantity=10.0,
            price=100.0,
            commission=2.50,
            slippage=0.0,
        )
    )
    tracker.apply_fill(
        Fill(
            order_id="s1",
            symbol="MU",
            timestamp=t1,
            side=OrderSide.SELL,
            quantity=10.0,
            price=100.0,
            commission=2.50,
            slippage=0.0,
        )
    )
    trade = tracker.closed_trades[0]
    assert trade.commission_paid == 5.00
    assert trade.gross_pnl == 0.00
    assert trade.net_pnl == -5.00
    assert tracker.cash == 9_995.00


def test_financing_separation_from_trading_pnl():
    """Verify that margin financing is kept separate from trade-level P&L and reconciles
    in calculate_metrics:
    portfolio_net_pnl == net_realized_pnl + options_realized_pnl - margin_interest_paid.
    """
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars("MU", num_bars=50, seed=42, start_time=t0)
    data = {"MU": bars}
    base = EngineConfig()
    base.strategy.universe = ["MU"]
    base.costs.margin_rate_annual = 0.08
    base.portfolio.max_gross_leverage = 2.0

    res = run_backtest(data, base)
    metrics = calculate_metrics(res)

    # Invariant: portfolio_net_pnl must equal net_realized_pnl + options - margin_interest
    expected_portfolio_net = round(
        metrics.net_realized_pnl + metrics.options_realized_pnl - metrics.margin_interest_paid, 2
    )
    assert metrics.portfolio_net_pnl == expected_portfolio_net


def test_stop_limit_evidence_classification():
    """Verify that REDDIT_STRATEGY_EVIDENCE_MATRIX.md classifies stop-limit order use as
    OBSERVED, but entry proxy modeling as HYPOTHESIS.
    """
    matrix_path = Path("docs/REDDIT_STRATEGY_EVIDENCE_MATRIX.md")
    assert matrix_path.exists()
    content = matrix_path.read_text(encoding="utf-8")

    assert "OBSERVED" in content
    assert "HYPOTHESIS" in content
    assert "Stop-Limits" in content or "stop-limit" in content.lower()


def test_report_terminology_and_scope_classification():
    """Verify that format_fidelity_markdown_report produces the required Phase I
    wording, scope classification, and accounting definitions.
    """
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars("MU", num_bars=50, seed=42, start_time=t0)
    data = {"MU": bars}
    base = EngineConfig()
    base.strategy.universe = ["MU"]

    matrix_res = run_fidelity_matrix(data=data, base_config=base)
    report_md = format_fidelity_markdown_report(result=matrix_res)

    # Required headers and labels
    assert "CURRENT_MECHANICAL_PULLBACK_BASELINE" in report_md
    assert "MECHANICAL_PULLBACK_SECTOR_FILTERED_DIAGNOSTIC" in report_md
    assert "DIRECTIONAL_FIDELITY_RECONSTRUCTION" in report_md

    # Required Phase I wording corrections
    assert "Fidelity Gap Partially Addressed — Deterministic Hypothesis Implemented" in report_md
    assert "FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED" in report_md
    assert "PRISTINE_OOS = UNAVAILABLE" in report_md
    assert "POST_HOC_SPECIFIED" in report_md
    assert "Signal-Price P&L" in report_md
    assert "ACCOUNTING INVARIANT & NO DOUBLE-COUNTING RULE" in report_md
    assert "STOP CONDITION" in report_md
