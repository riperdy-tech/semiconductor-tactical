from datetime import datetime

from pydantic import BaseModel

from tactical_engine.data.models import AccountState, Fill, OrderSide, Position


class TradeRecord(BaseModel):
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    net_pnl: float
    exit_reason: str


class PortfolioTracker:
    def __init__(self, initial_cash: float):
        self.cash = initial_cash
        self.positions: dict[str, Position] = {}
        self.closed_trades: list[TradeRecord] = []
        self.entry_times: dict[str, datetime] = {}

    def apply_fill(self, fill: Fill, exit_reason: str = "") -> None:
        pos = self.positions.get(fill.symbol, Position(symbol=fill.symbol))
        if fill.side == OrderSide.BUY:
            total_qty = pos.quantity + fill.quantity
            total_cost = (pos.quantity * pos.avg_price) + (fill.quantity * fill.price)
            new_avg = total_cost / total_qty if total_qty > 0 else 0.0
            self.positions[fill.symbol] = Position(
                symbol=fill.symbol,
                quantity=total_qty,
                avg_price=round(new_avg, 4),
                realized_pnl=pos.realized_pnl,
            )
            self.cash -= (fill.quantity * fill.price) + fill.commission
            if fill.symbol not in self.entry_times:
                self.entry_times[fill.symbol] = fill.timestamp
        else:
            # Sell
            gross_pnl = (fill.price - pos.avg_price) * fill.quantity
            net_pnl = gross_pnl - fill.commission - fill.slippage
            self.closed_trades.append(
                TradeRecord(
                    symbol=fill.symbol,
                    entry_time=self.entry_times.get(fill.symbol, fill.timestamp),
                    exit_time=fill.timestamp,
                    entry_price=pos.avg_price,
                    exit_price=fill.price,
                    quantity=fill.quantity,
                    gross_pnl=round(gross_pnl, 2),
                    net_pnl=round(net_pnl, 2),
                    exit_reason=exit_reason,
                )
            )
            self.cash += (fill.quantity * fill.price) - fill.commission
            remaining_qty = max(0.0, pos.quantity - fill.quantity)
            if remaining_qty == 0:
                self.positions.pop(fill.symbol, None)
                self.entry_times.pop(fill.symbol, None)
            else:
                self.positions[fill.symbol] = Position(
                    symbol=fill.symbol,
                    quantity=remaining_qty,
                    avg_price=pos.avg_price,
                    realized_pnl=pos.realized_pnl + net_pnl,
                )

    def get_account_state(
        self, timestamp: datetime, current_prices: dict[str, float]
    ) -> AccountState:
        equity = self.cash
        for sym, pos in self.positions.items():
            price = current_prices.get(sym, pos.avg_price)
            equity += pos.quantity * price
        return AccountState(
            timestamp=timestamp,
            cash=round(self.cash, 2),
            positions=self.positions.copy(),
            equity=round(equity, 2),
        )
