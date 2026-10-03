from datetime import UTC, datetime

from tactical_engine.config import CostConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
from tactical_engine.execution.simulator import ExecutionSimulator


def test_order_fill_next_bar_open_with_slippage():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=UTC)
    order = Order(
        order_id="ord-1",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=100.0,
    )
    next_bar = Bar(
        symbol="MU",
        timestamp=t1,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=50000.0,
    )
    cfg = CostConfig(
        equity_slippage_bps=10.0,
        market_impact_bps_per_1pct_volume=0.0,
        equity_commission_bps=0.0,
    )
    sim = ExecutionSimulator(cost_config=cfg)

    fill = sim.execute_order(order, next_bar)
    assert fill is not None
    # 10 bps slippage on $100 buy = +$0.10 -> fill at 100.10
    assert fill.price == 100.10
    assert fill.quantity == 100.0
    assert fill.timestamp == t1


def test_order_fill_with_market_impact():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=UTC)
    order = Order(
        order_id="ord-2",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=100.0,
    )
    next_bar = Bar(
        symbol="MU",
        timestamp=t1,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=50000.0,
    )
    # 10 bps base + 0.2% volume * 10 bps = 12 bps total
    cfg = CostConfig(
        equity_slippage_bps=10.0,
        market_impact_bps_per_1pct_volume=10.0,
        equity_commission_bps=0.0,
    )
    sim = ExecutionSimulator(cost_config=cfg)
    fill = sim.execute_order(order, next_bar)
    assert fill is not None
    assert fill.price == 100.12


def test_stop_limit_buy_triggers_and_fills_within_limit():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=UTC)
    order = Order(
        order_id="ord-sl-1",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        order_type=OrderType.STOP_LIMIT,
        quantity=100.0,
        stop_price=101.0,
        limit_price=101.50,
    )
    bar = Bar(
        symbol="MU",
        timestamp=t1,
        open=100.5,
        high=101.2,
        low=100.4,
        close=101.1,
        volume=50000.0,
    )
    cfg = CostConfig(equity_slippage_bps=0.0, market_impact_bps_per_1pct_volume=0.0)
    sim = ExecutionSimulator(cfg)
    fill = sim.execute_order(order, bar)
    assert fill is not None
    assert fill.price == 101.0  # triggered at stop price 101.0, within limit 101.50


def test_stop_limit_buy_untriggered():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=UTC)
    order = Order(
        order_id="ord-sl-2",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        order_type=OrderType.STOP_LIMIT,
        quantity=100.0,
        stop_price=102.0,
        limit_price=102.50,
    )
    bar = Bar(
        symbol="MU",
        timestamp=t1,
        open=100.5,
        high=101.5,
        low=100.4,
        close=101.1,
        volume=50000.0,
    )
    cfg = CostConfig(equity_slippage_bps=0.0, market_impact_bps_per_1pct_volume=0.0)
    sim = ExecutionSimulator(cfg)
    fill = sim.execute_order(order, bar)
    assert fill is None  # High 101.5 did not reach stop 102.0


def test_stop_limit_buy_gaps_above_limit_fails_to_fill():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=UTC)
    order = Order(
        order_id="ord-sl-3",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        order_type=OrderType.STOP_LIMIT,
        quantity=100.0,
        stop_price=101.0,
        limit_price=101.20,
    )
    bar = Bar(
        symbol="MU",
        timestamp=t1,
        open=102.0,
        high=103.0,
        low=101.8,
        close=102.5,
        volume=50000.0,
    )
    cfg = CostConfig(equity_slippage_bps=0.0, market_impact_bps_per_1pct_volume=0.0)
    sim = ExecutionSimulator(cfg)
    fill = sim.execute_order(order, bar)
    assert fill is None  # Gapped through limit price (low 101.8 > limit 101.20)


def test_stop_limit_sell_triggers_and_fills():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=UTC)
    order = Order(
        order_id="ord-sl-4",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.SELL,
        order_type=OrderType.STOP_LIMIT,
        quantity=100.0,
        stop_price=99.0,
        limit_price=98.50,
    )
    bar = Bar(
        symbol="MU",
        timestamp=t1,
        open=99.5,
        high=99.6,
        low=98.8,
        close=98.9,
        volume=50000.0,
    )
    cfg = CostConfig(equity_slippage_bps=0.0, market_impact_bps_per_1pct_volume=0.0)
    sim = ExecutionSimulator(cfg)
    fill = sim.execute_order(order, bar)
    assert fill is not None
    assert fill.price == 99.0


def test_stop_limit_sell_gaps_below_limit_fails_to_fill():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=UTC)
    order = Order(
        order_id="ord-sl-5",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.SELL,
        order_type=OrderType.STOP_LIMIT,
        quantity=100.0,
        stop_price=99.0,
        limit_price=98.50,
    )
    bar = Bar(
        symbol="MU",
        timestamp=t1,
        open=97.0,
        high=98.0,
        low=96.5,
        close=97.5,
        volume=50000.0,
    )
    cfg = CostConfig(equity_slippage_bps=0.0, market_impact_bps_per_1pct_volume=0.0)
    sim = ExecutionSimulator(cfg)
    fill = sim.execute_order(order, bar)
    assert fill is None  # Gapped through limit floor (high 98.0 < limit 98.50)
