from datetime import datetime

from pydantic import BaseModel

from tactical_engine.data.models import AccountState, Fill, OrderSide, Position
from tactical_engine.options.contracts import CoveredCallRecord, OptionPosition
from tactical_engine.portfolio.margin import calculate_margin_debt, calculate_margin_interest


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
    slippage_paid: float = 0.0
    commission_paid: float = 0.0


class LayerRecord(BaseModel, frozen=True):
    layer_number: int
    signal_time: datetime
    fill_time: datetime
    intended_price: float
    fill_price: float
    quantity: float
    incremental_risk: float
    aggregate_risk: float


class PortfolioTracker:
    def __init__(self, initial_cash: float):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: dict[str, Position] = {}
        self.closed_trades: list[TradeRecord] = []
        self.entry_times: dict[str, datetime] = {}
        self.entry_commissions: dict[str, float] = {}
        self.entry_slippage: dict[str, float] = {}
        self.layers_by_symbol: dict[str, list[LayerRecord]] = {}
        self.margin_interest_paid: float = 0.0
        self.peak_margin_debt: float = 0.0
        self.margin_call_count: int = 0
        self.forced_liquidation_count: int = 0
        # Options state
        self.covered_calls: dict[str, OptionPosition] = {}
        self.options_premium_collected: float = 0.0
        self.options_realized_pnl: float = 0.0
        self.covered_call_records: list[CoveredCallRecord] = []

    def accrue_margin_interest(self, rate_annual: float, elapsed_seconds: float) -> float:
        debt = calculate_margin_debt(self.cash)
        if debt > self.peak_margin_debt:
            self.peak_margin_debt = debt
        if debt > 0 and rate_annual > 0:
            interest = calculate_margin_interest(debt, rate_annual, elapsed_seconds)
            self.cash -= interest
            self.margin_interest_paid += interest
            return interest
        return 0.0

    def apply_fill(
        self, fill: Fill, exit_reason: str = "", stop_price: float | None = None
    ) -> None:
        if "forced_liquidation" in exit_reason:
            self.forced_liquidation_count += 1

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
            debt = calculate_margin_debt(self.cash)
            if debt > self.peak_margin_debt:
                self.peak_margin_debt = debt
            if fill.symbol not in self.entry_times:
                self.entry_times[fill.symbol] = fill.timestamp
            self.entry_commissions[fill.symbol] = (
                self.entry_commissions.get(fill.symbol, 0.0) + fill.commission
            )
            self.entry_slippage[fill.symbol] = (
                self.entry_slippage.get(fill.symbol, 0.0) + fill.slippage
            )

            # Record Layer State
            existing_layers = self.layers_by_symbol.get(fill.symbol, [])
            layer_num = len(existing_layers) + 1
            risk_per_share = (
                (fill.price - stop_price)
                if stop_price and stop_price < fill.price
                else (fill.price * 0.02)
            )
            inc_risk = risk_per_share * fill.quantity
            agg_risk = sum(layer.incremental_risk for layer in existing_layers) + inc_risk

            layer_rec = LayerRecord(
                layer_number=layer_num,
                signal_time=self.entry_times.get(fill.symbol, fill.timestamp),
                fill_time=fill.timestamp,
                intended_price=fill.price,
                fill_price=fill.price,
                quantity=fill.quantity,
                incremental_risk=round(inc_risk, 2),
                aggregate_risk=round(agg_risk, 2),
            )
            if fill.symbol not in self.layers_by_symbol:
                self.layers_by_symbol[fill.symbol] = []
            self.layers_by_symbol[fill.symbol].append(layer_rec)
        else:
            # Sell: gross_pnl uses fill.price (which already includes market slippage)
            gross_pnl = (fill.price - pos.avg_price) * fill.quantity
            alloc_ratio = (fill.quantity / pos.quantity) if pos.quantity > 0 else 1.0
            entry_comm = self.entry_commissions.get(fill.symbol, 0.0) * alloc_ratio
            entry_slip = self.entry_slippage.get(fill.symbol, 0.0) * alloc_ratio
            total_comm = round(entry_comm + fill.commission, 4)
            total_slip = round(entry_slip + fill.slippage, 4)

            # Net P&L: fill prices already reflect market slippage; only commissions are subtracted
            net_pnl = gross_pnl - total_comm

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
                    slippage_paid=round(total_slip, 2),
                    commission_paid=round(total_comm, 2),
                )
            )
            self.cash += (fill.quantity * fill.price) - fill.commission
            remaining_qty = max(0.0, pos.quantity - fill.quantity)
            if remaining_qty == 0:
                self.positions.pop(fill.symbol, None)
                self.entry_times.pop(fill.symbol, None)
                self.entry_commissions.pop(fill.symbol, None)
                self.entry_slippage.pop(fill.symbol, None)
                self.layers_by_symbol.pop(fill.symbol, None)
            else:
                self.entry_commissions[fill.symbol] = (
                    self.entry_commissions.get(fill.symbol, 0.0) - entry_comm
                )
                self.entry_slippage[fill.symbol] = (
                    self.entry_slippage.get(fill.symbol, 0.0) - entry_slip
                )
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
        debt = calculate_margin_debt(self.cash)
        return AccountState(
            timestamp=timestamp,
            cash=round(self.cash, 2),
            positions=self.positions.copy(),
            margin_debt=round(debt, 2),
            equity=round(equity, 2),
        )
