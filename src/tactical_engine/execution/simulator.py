from tactical_engine.config import CostConfig
from tactical_engine.data.models import Bar, Fill, Order, OrderSide, OrderType
from tactical_engine.execution.slippage import calculate_fill_price


class ExecutionSimulator:
    def __init__(self, cost_config: CostConfig):
        self.cost_config = cost_config

    def execute_order(self, order: Order, bar: Bar) -> Fill | None:
        if order.symbol != bar.symbol:
            return None

        # Liquidity constraint: order capped at 10% of bar volume if volume > 0
        fill_qty = order.quantity
        if bar.volume > 0 and fill_qty > (bar.volume * 0.10):
            fill_qty = bar.volume * 0.10

        if fill_qty <= 0:
            return None

        # Default: market orders fill at next bar open
        base_price = bar.open
        if order.order_type == OrderType.LIMIT and order.limit_price is not None:
            if order.side == OrderSide.BUY and bar.low > order.limit_price:
                return None
            if order.side == OrderSide.SELL and bar.high < order.limit_price:
                return None
            base_price = order.limit_price

        fill_price, slippage_dollars = calculate_fill_price(
            base_price=base_price,
            side=order.side,
            quantity=fill_qty,
            bar_volume=bar.volume,
            cost_config=self.cost_config,
        )

        commission = fill_qty * fill_price * (self.cost_config.equity_commission_bps / 10_000.0)

        return Fill(
            order_id=order.order_id,
            symbol=order.symbol,
            timestamp=bar.timestamp,
            side=order.side,
            quantity=fill_qty,
            price=fill_price,
            commission=round(commission, 4),
            slippage=round(slippage_dollars, 4),
        )
