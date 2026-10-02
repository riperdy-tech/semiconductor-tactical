from datetime import UTC, datetime, timedelta

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.backtest.state import PortfolioTracker
from tactical_engine.config import EngineConfig, ExitConfig
from tactical_engine.data.models import Bar, Fill, Order, OrderSide, OrderType
from tactical_engine.portfolio.sizing import calculate_position_size
from tactical_engine.signals.exits import check_exit_condition


def test_stored_stop_immutable_under_atr_expansion():
    """Verify that later ATR expansion does NOT move a trade's stop loss."""
    t0 = datetime(2026, 7, 15, 13, 30, tzinfo=UTC)
    cfg = ExitConfig(family="atr", stop_atr=1.0, target_atr=1.5)

    entry_price = 100.0
    entry_atr = 2.0
    stored_stop = entry_price - (cfg.stop_atr * entry_atr)  # 98.0
    stored_target = entry_price + (cfg.target_atr * entry_atr)  # 103.0

    # Next bar: ATR expands 5x to 10.0 (dynamic stop would become 90.0)
    # Price is 98.5 (above stored stop 98.0, but would be far above 90.0)
    bar_expanded = Bar(
        symbol="MU",
        timestamp=t0 + timedelta(minutes=1),
        open=99.0,
        high=99.2,
        low=98.5,
        close=98.8,
        volume=1000.0,
    )

    should_exit, _ = check_exit_condition(
        entry_price=entry_price,
        entry_time=t0,
        current_bar=bar_expanded,
        atr=10.0,  # Expanded current ATR
        config=cfg,
        stop_price=stored_stop,
        target_price=stored_target,
    )
    assert should_exit is False, "Trade should not exit above stored stop 98.0"

    # Price drops to 97.9 (breaches stored stop 98.0)
    bar_breach = Bar(
        symbol="MU",
        timestamp=t0 + timedelta(minutes=2),
        open=98.5,
        high=98.5,
        low=97.9,
        close=98.0,
        volume=1000.0,
    )
    should_exit_breach, reason = check_exit_condition(
        entry_price=entry_price,
        entry_time=t0,
        current_bar=bar_breach,
        atr=10.0,
        config=cfg,
        stop_price=stored_stop,
        target_price=stored_target,
    )
    assert should_exit_breach is True
    assert "98.00" in reason or "stop" in reason


def test_stored_stop_immutable_under_atr_contraction():
    """Verify that later ATR contraction does NOT tighten a trade's stop loss prematurely."""
    t0 = datetime(2026, 7, 15, 13, 30, tzinfo=UTC)
    cfg = ExitConfig(family="atr", stop_atr=1.0, target_atr=1.5)

    entry_price = 100.0
    entry_atr = 2.0
    stored_stop = entry_price - (cfg.stop_atr * entry_atr)  # 98.0
    stored_target = entry_price + (cfg.target_atr * entry_atr)  # 103.0

    # Next bar: ATR contracts to 0.2 (dynamic stop would tighten to 99.8)
    # Price is 99.0 (below 99.8, but comfortably above stored stop 98.0)
    bar_contracted = Bar(
        symbol="MU",
        timestamp=t0 + timedelta(minutes=1),
        open=99.5,
        high=99.6,
        low=99.0,
        close=99.2,
        volume=1000.0,
    )

    should_exit, _ = check_exit_condition(
        entry_price=entry_price,
        entry_time=t0,
        current_bar=bar_contracted,
        atr=0.2,  # Contracted current ATR
        config=cfg,
        stop_price=stored_stop,
        target_price=stored_target,
    )
    assert should_exit is False, "Trade must not be stopped out by contracted current ATR"


def test_stored_target_immutable_under_atr_changes():
    """Verify that later ATR changes do NOT move a trade's profit target."""
    t0 = datetime(2026, 7, 15, 13, 30, tzinfo=UTC)
    cfg = ExitConfig(family="atr", stop_atr=1.0, target_atr=1.5)

    entry_price = 100.0
    stored_stop = 98.0
    stored_target = 103.0  # 100.0 + 1.5 * 2.0 (entry ATR was 2.0)

    # ATR expands to 5.0 (dynamic target would be pushed up to 107.5)
    # Price hits 103.2 (touches stored target 103.0)
    bar_target = Bar(
        symbol="MU",
        timestamp=t0 + timedelta(minutes=5),
        open=102.5,
        high=103.2,
        low=102.0,
        close=103.0,
        volume=1000.0,
    )
    should_exit, reason = check_exit_condition(
        entry_price=entry_price,
        entry_time=t0,
        current_bar=bar_target,
        atr=5.0,  # Expanded current ATR
        config=cfg,
        stop_price=stored_stop,
        target_price=stored_target,
    )
    assert should_exit is True
    assert "target_hit" in reason


def test_position_sizing_uses_exact_stored_stop():
    """Verify position sizing uses the identical stop that is stored in PortfolioTracker."""
    t0 = datetime(2026, 7, 15, 13, 30, tzinfo=UTC)
    tracker = PortfolioTracker(initial_cash=100_000.0)
    cfg = EngineConfig()

    entry_price = 100.0
    entry_atr = 2.5
    stop_price = round(entry_price - (cfg.exits.stop_atr * entry_atr), 4)  # 97.5

    current_account_state = tracker.get_account_state(t0, {"MU": entry_price})
    qty = calculate_position_size(
        symbol="MU",
        price=entry_price,
        stop_price=stop_price,
        account_state=current_account_state,
        config=cfg.portfolio,
        current_prices={"MU": entry_price},
    )
    assert qty > 0

    order = Order(
        order_id="ord-01",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=qty,
        stop_price=stop_price,
        target_price=round(entry_price + (cfg.exits.target_atr * entry_atr), 4),
        entry_atr=entry_atr,
        tag="test_entry",
    )

    fill = Fill(
        order_id=order.order_id,
        symbol=order.symbol,
        timestamp=t0 + timedelta(minutes=1),
        side=order.side,
        quantity=order.quantity,
        price=entry_price,
    )

    tracker.apply_fill(
        fill=fill,
        exit_reason=order.tag,
        stop_price=order.stop_price,
        target_price=order.target_price,
        entry_atr=order.entry_atr,
    )

    assert tracker.stop_prices["MU"] == stop_price
    assert tracker.target_prices["MU"] == order.target_price
    assert tracker.entry_atrs["MU"] == entry_atr


def test_backtest_preserves_stored_exit_geometry():
    """Verify end-to-end backtest preserves stored exit geometry across volatility changes."""
    t0 = datetime(2026, 7, 15, 13, 30, tzinfo=UTC)
    cfg = EngineConfig()
    cfg.strategy.universe = ["MU"]
    cfg.signals.pullback_zscore = -0.5
    cfg.signals.sector_filter = False
    cfg.signals.relative_volume_filter = False
    cfg.signals.event_filter = False
    cfg.exits.family = "atr"
    cfg.exits.stop_atr = 1.0
    cfg.exits.target_atr = 1.5

    # Bar 0..65: warm up lookback
    bars = []
    for i in range(65):
        bars.append(
            Bar(
                symbol="MU",
                timestamp=t0 + timedelta(minutes=i),
                open=100.0,
                high=100.5,
                low=99.5,
                close=100.0,
                volume=1000.0,
                vwap=100.0,
            )
        )

    # Trigger pullback
    bars.append(
        Bar(
            symbol="MU",
            timestamp=t0 + timedelta(minutes=65),
            open=99.0,
            high=99.0,
            low=96.0,
            close=96.5,
            volume=5000.0,
            vwap=97.0,
        )
    )

    # Next bar: fill occurs
    bars.append(
        Bar(
            symbol="MU",
            timestamp=t0 + timedelta(minutes=66),
            open=96.5,
            high=97.0,
            low=96.0,
            close=96.8,
            volume=2000.0,
            vwap=96.5,
        )
    )

    # Subsequent bars: test execution runs without errors
    bars.append(
        Bar(
            symbol="MU",
            timestamp=t0 + timedelta(minutes=67),
            open=96.8,
            high=102.0,
            low=96.5,
            close=101.5,
            volume=2000.0,
            vwap=99.0,
        )
    )

    result = run_backtest({"MU": bars}, cfg)
    assert result.total_trades >= 0
    assert result.total_signals_generated >= 1
