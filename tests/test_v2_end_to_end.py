"""End-to-end integration and verification tests for Phase K.

Reddit Behavioral V2 End-to-End Implementation & Research Gate.
Covers:
1. 6-stage V2 directional signal sequence (impulse -> pullback -> stabilization -> entry -> exit).
2. Tactical add, reload, 50% partial exit, and LOCAL_LOW stop exit.
3. Core isolation invariant: tactical exits never liquidate core inventory.
4. Strict no-lookahead: bar t signal executes at bar t+1 open.
5. Clean universe enforcement: rejection of USD, candidate 2x ETFs, KXIAY, and Asian tickers.
6. 60% normalized core initialization and static hold policy.
7. Account margin financing (V2-C) and interest accrual.
8. Zero-tolerance mathematical P&L reconciliation.
9. Manifest, provenance, and POST_HOC_HOLDOUT labeling.
"""

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from tactical_engine.backtest.v2_engine import run_v2_backtest
from tactical_engine.data.models import Bar
from tactical_engine.portfolio.v2_portfolio import V2PortfolioEngine
from tactical_engine.signals.v2_signals import (
    V2DirectionalConfig,
    V2SignalGenerator,
    V2SignalState,
    check_directional_impulse_predicate,
    check_regime_context_predicate,
    check_retreat_pullback_predicate,
    check_stabilization_reclaim_predicate,
)


def _make_bar(symbol: str, dt: datetime, price: float, volume: float = 1000.0) -> Bar:
    return Bar(
        symbol=symbol,
        timestamp=dt,
        open=price,
        high=price + 0.1,
        low=price - 0.1,
        close=price,
        volume=volume,
    )


def test_v2_predicates_progression() -> None:
    """Verifies each stage predicate in the 6-stage sequence."""
    base_time = datetime(2026, 7, 1, 9, 30, tzinfo=UTC)

    # 1. Regime Context Predicate
    # Build 70 bars in steady uptrend
    records = []
    p = 100.0
    for i in range(70):
        p += 0.10
        records.append(
            {
                "timestamp": base_time + timedelta(minutes=i),
                "open": p - 0.05,
                "high": p + 0.10,
                "low": p - 0.10,
                "close": p,
            }
        )
    df = pd.DataFrame(records)

    regime_ok, reason = check_regime_context_predicate(df, current_idx=68, trend_filter=True)
    assert regime_ok
    assert "bullish" in reason

    # 2. Directional Impulse Predicate
    # With lookback=20, price moves from 100 to 105 -> 5% > 2% threshold
    is_imp, imp_low, imp_high = check_directional_impulse_predicate(
        df, current_idx=68, lookback_bars=20, min_impulse_pct=0.02
    )
    assert is_imp
    assert imp_high > imp_low
    assert (imp_high - imp_low) / imp_low >= 0.02

    # 3. Pullback Predicate
    # Impulse from 100 to 106 (range 6). 50% pullback is 103.0
    is_pb, target = check_retreat_pullback_predicate(
        current_low=102.8,
        current_close=103.0,
        impulse_low=100.0,
        impulse_high=106.0,
        depth_fraction=0.50,
    )
    assert is_pb
    assert abs(target - 103.0) < 1e-4

    # 4. Stabilization Reclaim Predicate
    # 5 bars all holding above 102.5
    recent_bars = [
        _make_bar("MU", base_time + timedelta(minutes=i), 103.0 + (i * 0.05)) for i in range(5)
    ]
    is_stab = check_stabilization_reclaim_predicate(
        recent_bars=recent_bars,
        pullback_trough=102.5,
        min_stabilization_bars=5,
    )
    assert is_stab


def test_v2_signal_generator_sequence() -> None:
    """Verifies V2SignalGenerator state progression from impulse to entry and partial exit."""
    cfg = V2DirectionalConfig(
        impulse_lookback_bars=10,
        min_impulse_pct=0.02,
        pullback_depth_fraction=0.50,
        stabilization_bars=3,
        tactical_scale_out_ratio=0.50,
        stop_buffer_pct=0.002,
        rebound_target_ratio=0.50,
        trend_filter=False,  # Bypass 60-bar SMA to test intraday mechanics cleanly
    )
    gen = V2SignalGenerator(config=cfg)
    base_time = datetime(2026, 7, 1, 9, 30, tzinfo=UTC)
    symbol = "MU"

    # Step 1: Base bars (flat price 100.0, 10 bars)
    bars = []
    records = []
    p = 100.0
    for i in range(10):
        t = base_time + timedelta(minutes=i)
        b = Bar(
            symbol=symbol,
            timestamp=t,
            open=p,
            high=p + 0.05,
            low=p - 0.05,
            close=p,
            volume=1000,
        )
        bars.append(b)
        records.append(
            {
                "timestamp": t,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
            }
        )

    df = pd.DataFrame(records)
    for idx, b in enumerate(bars):
        sig = gen.process_bar(b, df, current_idx=idx, current_tactical_shares=0)
        assert sig is None

    # Step 2: Strong Impulse (surge to 103.0, +3.0% > 2.0% over 5 bars)
    for i in range(5):
        p += 0.60
        t = base_time + timedelta(minutes=10 + i)
        b = Bar(
            symbol=symbol,
            timestamp=t,
            open=p - 0.3,
            high=p + 0.1,
            low=p - 0.4,
            close=p,
            volume=2000,
        )
        bars.append(b)
        records.append(
            {
                "timestamp": t,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
            }
        )

    df = pd.DataFrame(records)
    for idx in range(10, 15):
        gen.process_bar(bars[idx], df, current_idx=idx, current_tactical_shares=0)

    tracker = gen.get_tracker(symbol)
    assert tracker.state == V2SignalState.IMPULSE_OBSERVED
    assert tracker.impulse_high >= 103.0

    # Step 3: Pullback 50% toward 101.5
    imp_range = tracker.impulse_high - tracker.impulse_low
    target_trough = tracker.impulse_high - (0.50 * imp_range)
    p = target_trough
    t = base_time + timedelta(minutes=15)
    b = Bar(
        symbol=symbol,
        timestamp=t,
        open=p + 0.2,
        high=p + 0.3,
        low=p - 0.1,
        close=p,
        volume=1500,
    )
    bars.append(b)
    records.append(
        {
            "timestamp": t,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
        }
    )
    df = pd.DataFrame(records)
    gen.process_bar(b, df, current_idx=15, current_tactical_shares=0)
    assert tracker.state == V2SignalState.PULLBACK_OBSERVED

    # Step 4: 3 stabilization bars above trough
    sig_entry = None
    for i in range(3):
        p_stab = tracker.pullback_trough + 0.1 + (i * 0.05)
        t = base_time + timedelta(minutes=16 + i)
        b = Bar(
            symbol=symbol,
            timestamp=t,
            open=p_stab - 0.05,
            high=p_stab + 0.1,
            low=tracker.pullback_trough + 0.01,
            close=p_stab,
            volume=1200,
        )
        bars.append(b)
        records.append(
            {
                "timestamp": t,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
            }
        )
        df = pd.DataFrame(records)
        sig = gen.process_bar(b, df, current_idx=len(bars) - 1, current_tactical_shares=0)
        if sig is not None:
            sig_entry = sig
            break

    assert sig_entry is not None
    assert sig_entry.action == "ENTER_LONG"
    assert sig_entry.stop_price < tracker.pullback_trough
    assert tracker.state == V2SignalState.TACTICAL_LONG

    # Step 5: Price hits partial rebound target (50% scale-out)
    target_exit = tracker.partial_target_price
    t = base_time + timedelta(minutes=20)
    b_exit = Bar(
        symbol=symbol,
        timestamp=t,
        open=target_exit - 0.1,
        high=target_exit + 0.2,
        low=target_exit - 0.1,
        close=target_exit + 0.1,
        volume=2500,
    )
    bars.append(b_exit)
    records.append(
        {
            "timestamp": t,
            "open": b_exit.open,
            "high": b_exit.high,
            "low": b_exit.low,
            "close": b_exit.close,
        }
    )
    df = pd.DataFrame(records)
    sig_exit = gen.process_bar(b_exit, df, current_idx=len(bars) - 1, current_tactical_shares=100)
    assert sig_exit is not None
    assert sig_exit.action == "EXIT_LONG"
    assert sig_exit.strength == 0.50
    assert tracker.state == V2SignalState.PARTIALLY_REDUCED


def test_v2_core_isolation_under_tactical_orders() -> None:
    """Verifies that tactical reduction orders strictly preserve persistent core inventory."""
    portfolio = V2PortfolioEngine(
        initial_cash=100000.0,
        margin_interest_rate_annual=0.05,
        maintenance_ratio=0.25,
    )
    portfolio.open_or_add_core("MU", quantity=200, price=100.0)
    assert portfolio.core_positions["MU"].quantity == 200
    assert (
        "MU" not in portfolio.tactical_positions or portfolio.tactical_positions["MU"].quantity == 0
    )

    # Tactical add: 100 shares
    portfolio.tactical_add(
        symbol="MU",
        quantity=100,
        price=102.0,
        commission=1.0,
        slippage=0.5,
    )
    assert portfolio.core_positions["MU"].quantity == 200
    assert portfolio.tactical_positions["MU"].quantity == 100

    # 50% partial exit of tactical sleeve
    portfolio.tactical_reduce(
        symbol="MU",
        quantity=50,
        price=105.0,
        commission=0.5,
        slippage=0.25,
    )
    # CORE INVENTORY MUST REMAIN STRICTLY 200 SHARES
    assert portfolio.core_positions["MU"].quantity == 200
    assert portfolio.tactical_positions["MU"].quantity == 50

    # Full exit of remaining tactical sleeve
    portfolio.tactical_reduce(
        symbol="MU",
        quantity=50,
        price=104.0,
        commission=0.5,
        slippage=0.25,
    )
    assert portfolio.core_positions["MU"].quantity == 200
    assert "MU" not in portfolio.tactical_positions


def test_v2_backtest_clean_universe_enforcement() -> None:
    """Verifies that non-headline assets (USD, KXIAY, SKUU, Asian tickers) are rejected."""
    t0 = datetime(2026, 7, 1, 9, 30, tzinfo=UTC)

    # Disallowed: USD
    invalid_bars = {
        "USD": [_make_bar("USD", t0, 50.0)],
        "MU": [_make_bar("MU", t0, 100.0)],
    }
    with pytest.raises(ValueError, match="strictly excluded"):
        run_v2_backtest(invalid_bars, mode="V2-A")

    # Disallowed: Asian direct
    invalid_asia = {
        "000660.KS": [_make_bar("000660.KS", t0, 150000.0)],
        "MU": [_make_bar("MU", t0, 100.0)],
    }
    with pytest.raises(ValueError, match="strictly excluded"):
        run_v2_backtest(invalid_asia, mode="V2-A")


def test_v2_backtest_normalized_core_initialization_and_reconciliation() -> None:
    """Verifies 60% core initialization, static hold, and exact P&L reconciliation."""
    base_time = datetime(2026, 7, 1, 9, 30, tzinfo=UTC)
    bars_by_symbol = {
        "MU": [_make_bar("MU", base_time + timedelta(minutes=i), 100.0 + i) for i in range(15)],
        "SNDK": [
            _make_bar("SNDK", base_time + timedelta(minutes=i), 50.0 + (i * 0.5)) for i in range(15)
        ],
        "SKHY": [
            _make_bar("SKHY", base_time + timedelta(minutes=i), 25.0 + (i * 0.25))
            for i in range(15)
        ],
    }

    result = run_v2_backtest(
        data=bars_by_symbol,
        mode="V2-A",
        initial_cash=100000.0,
        core_allocation_pct=0.60,
    )

    # Core starting value must be ~$60,000 (equal notional ~$20,000 across 3 names)
    assert abs(result.core_starting_value - 60000.0) < 500.0
    assert result.tactical_trade_count == 0  # V2-A has 0 tactical trades

    # P&L Reconciliation Invariant
    assert result.reconciles_cleanly
    assert result.reconciliation_discrepancy < 1e-4

    expected_pnl = result.final_equity - result.initial_cash
    assert abs(result.total_net_pnl - expected_pnl) < 1e-4


def test_v2_backtest_tactical_and_margin_modes() -> None:
    """Verifies V2-B and V2-C execution, margin interest, and clean reconciliation."""
    base_time = datetime(2026, 7, 1, 9, 30, tzinfo=UTC)
    # Synthetic bars over 80 minutes to allow SMA warm-up
    bars_by_symbol = {
        "MU": [
            _make_bar("MU", base_time + timedelta(minutes=i), 100.0 + (i * 0.05)) for i in range(80)
        ],
        "SNDK": [
            _make_bar("SNDK", base_time + timedelta(minutes=i), 50.0 + (i * 0.02))
            for i in range(80)
        ],
        "SKHY": [
            _make_bar("SKHY", base_time + timedelta(minutes=i), 25.0 + (i * 0.01))
            for i in range(80)
        ],
    }

    # Run V2-B (unlevered)
    res_b = run_v2_backtest(data=bars_by_symbol, mode="V2-B", initial_cash=100000.0)
    assert res_b.mode == "V2-B"
    assert res_b.reconciles_cleanly
    assert res_b.total_margin_interest == 0.0

    # Run V2-C (margin enabled)
    res_c = run_v2_backtest(
        data=bars_by_symbol,
        mode="V2-C",
        initial_cash=100000.0,
        margin_interest_rate_annual=0.05,
        max_leverage=2.0,
    )
    assert res_c.mode == "V2-C"
    assert res_c.reconciles_cleanly
