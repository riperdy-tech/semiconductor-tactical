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

        base_price: float = bar.open

        if order.order_type == OrderType.MARKET:
            base_price = bar.open

        elif order.order_type == OrderType.LIMIT:
            if order.limit_price is None:
                return None
            if order.side == OrderSide.BUY:
                if bar.low > order.limit_price:
                    return None
                base_price = min(bar.open, order.limit_price)
            else:
                if bar.high < order.limit_price:
                    return None
                base_price = max(bar.open, order.limit_price)

        elif order.order_type == OrderType.STOP:
            if order.stop_price is None:
                return None
            if order.side == OrderSide.BUY:
                if bar.high < order.stop_price:
                    return None
                base_price = max(bar.open, order.stop_price)
            else:
                if bar.low > order.stop_price:
                    return None
                base_price = min(bar.open, order.stop_price)

        elif order.order_type == OrderType.STOP_LIMIT:
            if order.stop_price is None or order.limit_price is None:
                return None
            if order.side == OrderSide.BUY:
                # Trigger check: bar must reach or exceed stop trigger
                if bar.high < order.stop_price and bar.open < order.stop_price:
                    return None
                # Limit check: bar must have traded at or below limit price
                if bar.low > order.limit_price:
                    # Gapped above limit price without fill opportunity
                    return None
                # Base price selection
                if bar.open >= order.stop_price:
                    base_price = bar.open if bar.open <= order.limit_price else order.limit_price
                else:
                    base_price = min(order.stop_price, order.limit_price)
            else:
                # Trigger check: bar must reach or drop below stop trigger
                if bar.low > order.stop_price and bar.open > order.stop_price:
                    return None
                # Limit check: bar must have traded at or above limit price
                if bar.high < order.limit_price:
                    # Gapped below limit price without fill opportunity
                    return None
                # Base price selection
                if bar.open <= order.stop_price:
                    base_price = bar.open if bar.open >= order.limit_price else order.limit_price
                else:
                    base_price = max(order.stop_price, order.limit_price)

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
            reference_price=base_price,
            commission=round(commission, 4),
            slippage=round(slippage_dollars, 4),
        )
