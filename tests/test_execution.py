from datetime import datetime, timezone
from tactical_engine.config import CostConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
from tactical_engine.execution.simulator import ExecutionSimulator


def test_order_fill_next_bar_open_with_slippage():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=timezone.utc)
    order = Order(
        order_id="ord-1",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=100.0,
    )
    next_bar = Bar(symbol="MU", timestamp=t1, open=100.0, high=101.0, low=99.0, close=100.5, volume=50000.0)
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
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=timezone.utc)
    order = Order(
        order_id="ord-2",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=100.0,
    )
    next_bar = Bar(symbol="MU", timestamp=t1, open=100.0, high=101.0, low=99.0, close=100.5, volume=50000.0)
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
