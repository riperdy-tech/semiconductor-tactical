"""Reddit Behavioral Replication V2 Portfolio Process Engine.

Models the multi-layer portfolio architecture described by the primary Reddit source:
1. Persistent Core Holdings (long-term high-beta semiconductor memory inventory: MU, SNDK, SKHY).
2. Tactical Trading Sleeve (active add, reload, partial/full reduction, re-entry around core).
3. Covered-Call Overlay (short-dated calls written during strength, repurchased on pullback,
   strictly attached to owned unencumbered shares).
4. Account-Level Margin (financing across core + tactical, maintenance requirements, liquidation).
5. Segregated Profit Withdrawals (tracked for capital accounting without inflating strategy return).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from tactical_engine.data.models import Order, OrderSide, OrderType


class V2HoldingSleeve(StrEnum):
    CORE = "CORE"
    TACTICAL = "TACTICAL"


class CoveredCallStatus(StrEnum):
    OPEN = "OPEN"
    BOUGHT_BACK = "BOUGHT_BACK"
    EXPIRED_OTM = "EXPIRED_OTM"
    ASSIGNED = "ASSIGNED"


@dataclass
class V2PositionRecord:
    symbol: str
    sleeve: V2HoldingSleeve
    quantity: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0
    encumbered_shares_for_calls: float = 0.0

    @property
    def available_shares_for_calls(self) -> float:
        return max(0.0, self.quantity - self.encumbered_shares_for_calls)

    def add_shares(self, qty: float, price: float) -> None:
        if qty <= 0:
            raise ValueError(f"Quantity to add must be positive, got {qty}")
        if price < 0:
            raise ValueError(f"Price cannot be negative, got {price}")
        new_qty = self.quantity + qty
        if new_qty > 0:
            self.avg_price = (self.quantity * self.avg_price + qty * price) / new_qty
        self.quantity = new_qty

    def reduce_shares(self, qty: float, price: float) -> float:
        if qty <= 0:
            raise ValueError(f"Quantity to reduce must be positive, got {qty}")
        if qty > self.quantity + 1e-6:
            raise ValueError(
                f"Cannot reduce {qty} shares from position with only {self.quantity} shares"
            )
        qty = min(qty, self.quantity)
        trade_realized_pnl = (price - self.avg_price) * qty
        self.realized_pnl += trade_realized_pnl
        self.quantity -= qty
        if self.quantity < 1e-6:
            self.quantity = 0.0
            self.avg_price = 0.0
            self.encumbered_shares_for_calls = 0.0
        return trade_realized_pnl

    def market_value(self, current_price: float) -> float:
        return self.quantity * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        if self.quantity <= 0:
            return 0.0
        return (current_price - self.avg_price) * self.quantity


@dataclass
class V2CoveredCallRecord:
    contract_symbol: str
    underlying: str
    sleeve_source: V2HoldingSleeve
    contracts: float
    shares_covered: float
    strike: float
    expiration: datetime
    entry_time: datetime
    entry_premium_per_share: float
    exit_time: datetime | None = None
    exit_premium_per_share: float | None = None
    exit_reason: str | None = None
    realized_pnl: float = 0.0
    shares_delivered: float = 0.0
    status: CoveredCallStatus = CoveredCallStatus.OPEN

    @property
    def is_open(self) -> bool:
        return self.status == CoveredCallStatus.OPEN


@dataclass
class V2ProfitWithdrawal:
    timestamp: datetime
    amount: float
    note: str = ""


class V2PortfolioEngine:
    """Multi-layer portfolio tracker reproducing the Reddit behavioral architecture."""

    def __init__(
        self,
        initial_cash: float = 100_000.0,
        margin_interest_rate_annual: float = 0.05,
        maintenance_ratio: float = 0.25,
        max_leverage: float = 2.0,
    ) -> None:
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.margin_interest_rate_annual = margin_interest_rate_annual
        self.maintenance_ratio = maintenance_ratio
        self.max_leverage = max_leverage

        self.core_positions: dict[str, V2PositionRecord] = {}
        self.tactical_positions: dict[str, V2PositionRecord] = {}
        self.open_calls: dict[str, V2CoveredCallRecord] = {}
        self.closed_calls: list[V2CoveredCallRecord] = []
        self.withdrawals: list[V2ProfitWithdrawal] = []

        self.financing_interest_paid: float = 0.0
        self.commissions_paid: float = 0.0
        self.slippage_paid: float = 0.0

    # -------------------------------------------------------------------------
    # Core Positions
    # -------------------------------------------------------------------------
    def open_or_add_core(
        self,
        symbol: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> None:
        """Add to persistent core holding."""
        cost = quantity * price
        self.cash -= cost + commission
        self.commissions_paid += commission
        self.slippage_paid += slippage

        pos = self.core_positions.get(symbol)
        if pos is None:
            pos = V2PositionRecord(symbol=symbol, sleeve=V2HoldingSleeve.CORE)
            self.core_positions[symbol] = pos
        pos.add_shares(quantity, price)

    def reduce_core(
        self,
        symbol: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> float:
        """Reduce persistent core holding."""
        pos = self.core_positions.get(symbol)
        if pos is None or pos.quantity <= 0:
            raise ValueError(f"No active core position in {symbol} to reduce")
        if pos.available_shares_for_calls < quantity - 1e-6:
            raise ValueError(
                f"Cannot reduce {quantity} core shares of {symbol}: "
                f"{pos.encumbered_shares_for_calls} shares are encumbered by open covered calls"
            )
        pnl = pos.reduce_shares(quantity, price)
        proceeds = quantity * price
        self.cash += proceeds - commission
        self.commissions_paid += commission
        self.slippage_paid += slippage
        if pos.quantity == 0:
            del self.core_positions[symbol]
        return pnl

    # -------------------------------------------------------------------------
    # Tactical Trading Sleeve (Scalp / Swing Around Core)
    # -------------------------------------------------------------------------
    def tactical_add(
        self,
        symbol: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> None:
        """Add to tactical sleeve (separate from core holding)."""
        cost = quantity * price
        self.cash -= cost + commission
        self.commissions_paid += commission
        self.slippage_paid += slippage

        pos = self.tactical_positions.get(symbol)
        if pos is None:
            pos = V2PositionRecord(symbol=symbol, sleeve=V2HoldingSleeve.TACTICAL)
            self.tactical_positions[symbol] = pos
        pos.add_shares(quantity, price)

    def tactical_reduce(
        self,
        symbol: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> float:
        """Reduce tactical sleeve. Crucially, NEVER liquidates or alters persistent core."""
        pos = self.tactical_positions.get(symbol)
        if pos is None or pos.quantity <= 0:
            raise ValueError(f"No active tactical position in {symbol} to reduce")
        pnl = pos.reduce_shares(quantity, price)
        proceeds = quantity * price
        self.cash += proceeds - commission
        self.commissions_paid += commission
        self.slippage_paid += slippage
        if pos.quantity == 0:
            del self.tactical_positions[symbol]
        return pnl

    # -------------------------------------------------------------------------
    # Covered-Call Overlay (Attached to Owned Shares)
    # -------------------------------------------------------------------------
    def write_covered_call(
        self,
        underlying: str,
        contract_symbol: str,
        strike: float,
        expiration: datetime,
        contracts: float,
        premium_per_share: float,
        entry_time: datetime,
        sleeve_source: V2HoldingSleeve = V2HoldingSleeve.CORE,
        commission: float = 0.0,
    ) -> V2CoveredCallRecord:
        """Write short covered calls against owned unencumbered shares."""
        if contracts <= 0:
            raise ValueError(f"Contracts must be positive, got {contracts}")
        shares_needed = contracts * 100.0

        pos_dict = (
            self.core_positions
            if sleeve_source == V2HoldingSleeve.CORE
            else self.tactical_positions
        )
        pos = pos_dict.get(underlying)
        if pos is None or pos.available_shares_for_calls < shares_needed - 1e-6:
            avail = pos.available_shares_for_calls if pos else 0.0
            raise ValueError(
                f"Insufficient unencumbered {sleeve_source} shares in {underlying}: "
                f"need {shares_needed}, available {avail}"
            )

        pos.encumbered_shares_for_calls += shares_needed
        gross_premium = shares_needed * premium_per_share
        self.cash += gross_premium - commission
        self.commissions_paid += commission

        call_record = V2CoveredCallRecord(
            contract_symbol=contract_symbol,
            underlying=underlying,
            sleeve_source=sleeve_source,
            contracts=contracts,
            shares_covered=shares_needed,
            strike=strike,
            expiration=expiration,
            entry_time=entry_time,
            entry_premium_per_share=premium_per_share,
        )
        self.open_calls[contract_symbol] = call_record
        return call_record

    def repurchase_covered_call(
        self,
        contract_symbol: str,
        buyback_premium_per_share: float,
        exit_time: datetime,
        reason: str = "BUYBACK_PULLBACK",
        commission: float = 0.0,
    ) -> float:
        """Repurchase covered call on underlying pullback before expiration."""
        call = self.open_calls.get(contract_symbol)
        if call is None:
            raise ValueError(f"No open covered call with symbol {contract_symbol}")

        gross_buyback_cost = call.shares_covered * buyback_premium_per_share
        self.cash -= gross_buyback_cost + commission
        self.commissions_paid += commission

        # Unlock encumbered underlying shares
        pos_dict = (
            self.core_positions
            if call.sleeve_source == V2HoldingSleeve.CORE
            else self.tactical_positions
        )
        pos = pos_dict.get(call.underlying)
        if pos:
            pos.encumbered_shares_for_calls = max(
                0.0, pos.encumbered_shares_for_calls - call.shares_covered
            )

        opt_pnl = (
            call.entry_premium_per_share - buyback_premium_per_share
        ) * call.shares_covered
        call.exit_time = exit_time
        call.exit_premium_per_share = buyback_premium_per_share
        call.exit_reason = reason
        call.realized_pnl = opt_pnl
        call.status = CoveredCallStatus.BOUGHT_BACK

        del self.open_calls[contract_symbol]
        self.closed_calls.append(call)
        return opt_pnl

    def expire_covered_call(
        self,
        contract_symbol: str,
        exit_time: datetime,
    ) -> float:
        """Mark covered call expired OTM at expiration date."""
        call = self.open_calls.get(contract_symbol)
        if call is None:
            raise ValueError(f"No open covered call with symbol {contract_symbol}")

        # Unlock shares
        pos_dict = (
            self.core_positions
            if call.sleeve_source == V2HoldingSleeve.CORE
            else self.tactical_positions
        )
        pos = pos_dict.get(call.underlying)
        if pos:
            pos.encumbered_shares_for_calls = max(
                0.0, pos.encumbered_shares_for_calls - call.shares_covered
            )

        opt_pnl = call.entry_premium_per_share * call.shares_covered
        call.exit_time = exit_time
        call.exit_premium_per_share = 0.0
        call.exit_reason = "EXPIRED_OTM"
        call.realized_pnl = opt_pnl
        call.status = CoveredCallStatus.EXPIRED_OTM

        del self.open_calls[contract_symbol]
        self.closed_calls.append(call)
        return opt_pnl

    def assign_covered_call(
        self,
        contract_symbol: str,
        exit_time: datetime,
        commission: float = 0.0,
    ) -> tuple[float, float]:
        """Exercise / assignment: deliver underlying shares at strike price.

        Returns (option_realized_pnl, equity_realized_pnl).
        """
        call = self.open_calls.get(contract_symbol)
        if call is None:
            raise ValueError(f"No open covered call with symbol {contract_symbol}")

        pos_dict = (
            self.core_positions
            if call.sleeve_source == V2HoldingSleeve.CORE
            else self.tactical_positions
        )
        pos = pos_dict.get(call.underlying)
        if pos is None or pos.quantity < call.shares_covered - 1e-6:
            raise ValueError(
                f"Assignment failure: owned shares in {call.underlying} "
                f"less than {call.shares_covered}"
            )

        # Unlock and deliver shares at strike
        pos.encumbered_shares_for_calls = max(
            0.0, pos.encumbered_shares_for_calls - call.shares_covered
        )
        equity_pnl = pos.reduce_shares(call.shares_covered, call.strike)

        strike_proceeds = call.shares_covered * call.strike
        self.cash += strike_proceeds - commission
        self.commissions_paid += commission

        opt_pnl = call.entry_premium_per_share * call.shares_covered
        call.exit_time = exit_time
        call.exit_premium_per_share = 0.0
        call.exit_reason = "ASSIGNED"
        call.realized_pnl = opt_pnl
        call.shares_delivered = call.shares_covered
        call.status = CoveredCallStatus.ASSIGNED

        if pos.quantity == 0:
            del pos_dict[call.underlying]

        del self.open_calls[contract_symbol]
        self.closed_calls.append(call)
        return opt_pnl, equity_pnl

    # -------------------------------------------------------------------------
    # Margin & Capital Accounting
    # -------------------------------------------------------------------------
    def accrue_financing(self, elapsed_seconds: float) -> float:
        """Accrue margin debt financing cost if cash is negative."""
        margin_debt = self.margin_debt
        if margin_debt <= 0 or self.margin_interest_rate_annual <= 0 or elapsed_seconds <= 0:
            return 0.0
        year_fraction = elapsed_seconds / (365.0 * 86400.0)
        interest = margin_debt * self.margin_interest_rate_annual * year_fraction
        self.cash -= interest
        self.financing_interest_paid += interest
        return interest

    @property
    def margin_debt(self) -> float:
        return max(0.0, -self.cash)

    def total_positions_market_value(self, current_prices: dict[str, float]) -> float:
        core_val = sum(
            pos.market_value(current_prices.get(sym, pos.avg_price))
            for sym, pos in self.core_positions.items()
        )
        tact_val = sum(
            pos.market_value(current_prices.get(sym, pos.avg_price))
            for sym, pos in self.tactical_positions.items()
        )
        return core_val + tact_val

    def get_equity(
        self,
        current_prices: dict[str, float],
        current_call_prices: dict[str, float] | None = None,
    ) -> float:
        """Net account liquidation equity: cash + all equity positions - open option liabilities."""
        pos_val = self.total_positions_market_value(current_prices)
        opt_liability = 0.0
        if current_call_prices:
            for contract_sym, call in self.open_calls.items():
                price = current_call_prices.get(contract_sym, call.entry_premium_per_share)
                opt_liability += call.shares_covered * price
        return self.cash + pos_val - opt_liability

    def get_maintenance_requirement(self, current_prices: dict[str, float]) -> float:
        return self.total_positions_market_value(current_prices) * self.maintenance_ratio

    def is_margin_call(self, current_prices: dict[str, float]) -> bool:
        return self.get_equity(current_prices) < self.get_maintenance_requirement(current_prices)

    def get_buying_power(self, current_prices: dict[str, float]) -> float:
        eq = max(0.0, self.get_equity(current_prices))
        max_exposure = eq * self.max_leverage
        current_exposure = self.total_positions_market_value(current_prices)
        return max(0.0, max_exposure - current_exposure)

    def generate_margin_liquidation_orders(
        self,
        current_prices: dict[str, float],
        timestamp: datetime,
    ) -> list[Order]:
        """Generates forced liquidation orders when in margin call deficit.

        Prioritizes liquidating tactical positions first to preserve persistent core holdings.
        """
        eq = self.get_equity(current_prices)
        req = self.get_maintenance_requirement(current_prices)
        if eq >= req:
            return []

        deficit = req - eq
        orders: list[Order] = []
        remaining_deficit = deficit
        relief_per_dollar = 1.0 - self.maintenance_ratio

        # Liquidate tactical positions first
        sorted_tactical = sorted(
            self.tactical_positions.items(),
            key=lambda item: item[1].quantity * current_prices.get(item[0], item[1].avg_price),
            reverse=True,
        )
        for sym, pos in sorted_tactical:
            if pos.quantity <= 0:
                continue
            price = current_prices.get(sym, pos.avg_price)
            pos_val = pos.quantity * price
            dollars_to_liquidate = min(pos_val, remaining_deficit / relief_per_dollar)
            shares = min(pos.quantity, float(int(dollars_to_liquidate / price)) or 1.0)
            orders.append(
                Order(
                    order_id=str(uuid.uuid4())[:8],
                    symbol=sym,
                    timestamp=timestamp,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=shares,
                    tag=f"v2_forced_liquidation_tactical (deficit=${deficit:,.2f})",
                )
            )
            remaining_deficit -= shares * price * relief_per_dollar
            if remaining_deficit <= 0:
                return orders

        # If tactical is depleted and deficit remains, liquidate unencumbered core positions
        sorted_core = sorted(
            self.core_positions.items(),
            key=lambda item: item[1].available_shares_for_calls
            * current_prices.get(item[0], item[1].avg_price),
            reverse=True,
        )
        for sym, pos in sorted_core:
            avail = pos.available_shares_for_calls
            if avail <= 0:
                continue
            price = current_prices.get(sym, pos.avg_price)
            pos_val = avail * price
            dollars_to_liquidate = min(pos_val, remaining_deficit / relief_per_dollar)
            shares = min(avail, float(int(dollars_to_liquidate / price)) or 1.0)
            orders.append(
                Order(
                    order_id=str(uuid.uuid4())[:8],
                    symbol=sym,
                    timestamp=timestamp,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=shares,
                    tag=f"v2_forced_liquidation_core (deficit=${deficit:,.2f})",
                )
            )
            remaining_deficit -= shares * price * relief_per_dollar
            if remaining_deficit <= 0:
                break

        return orders

    # -------------------------------------------------------------------------
    # Profit Withdrawals (Segregated Capital Accounting)
    # -------------------------------------------------------------------------
    def record_withdrawal(self, amount: float, timestamp: datetime, note: str = "") -> None:
        """Record an explicit profit withdrawal.

        Segregated so that it does NOT artificially inflate or alter strategy returns.
        """
        if amount <= 0:
            raise ValueError(f"Withdrawal amount must be positive, got {amount}")
        if self.cash < amount:
            raise ValueError(
                f"Cannot withdraw ${amount:,.2f}: available cash is only ${self.cash:,.2f}"
            )
        self.cash -= amount
        self.withdrawals.append(
            V2ProfitWithdrawal(timestamp=timestamp, amount=amount, note=note)
        )

    @property
    def total_withdrawals(self) -> float:
        return sum(w.amount for w in self.withdrawals)

    # -------------------------------------------------------------------------
    # Strict P&L Reconciliation Invariant
    # -------------------------------------------------------------------------
    def reconcile_pnl_attribution(
        self,
        current_prices: dict[str, float],
        current_call_prices: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """Reconciles account P&L components against the fundamental accounting invariant:

        net_equity - initial_cash + total_withdrawals =
            core_realized_pnl + core_unrealized_pnl +
            tactical_realized_pnl + tactical_unrealized_pnl +
            covered_call_realized_pnl + covered_call_unrealized_pnl -
            financing_interest_paid - commissions_paid - slippage_paid
        """
        core_realized = sum(p.realized_pnl for p in self.core_positions.values())
        core_unrealized = sum(
            p.unrealized_pnl(current_prices.get(sym, p.avg_price))
            for sym, p in self.core_positions.items()
        )
        tact_realized = sum(p.realized_pnl for p in self.tactical_positions.values())
        tact_unrealized = sum(
            p.unrealized_pnl(current_prices.get(sym, p.avg_price))
            for sym, p in self.tactical_positions.items()
        )
        opt_realized = sum(c.realized_pnl for c in self.closed_calls)

        opt_unrealized = 0.0
        if current_call_prices:
            for contract_sym, call in self.open_calls.items():
                cur_price = current_call_prices.get(contract_sym, call.entry_premium_per_share)
                # Short call unrealized = entry_premium - current_price
                opt_unrealized += (call.entry_premium_per_share - cur_price) * call.shares_covered

        total_component_pnl = (
            core_realized
            + core_unrealized
            + tact_realized
            + tact_unrealized
            + opt_realized
            + opt_unrealized
            - self.financing_interest_paid
            - self.commissions_paid
        )

        eq = self.get_equity(current_prices, current_call_prices)
        total_accounting_pnl = eq - self.initial_cash + self.total_withdrawals

        discrepancy = abs(total_accounting_pnl - total_component_pnl)

        return {
            "initial_cash": self.initial_cash,
            "ending_cash": self.cash,
            "ending_equity": eq,
            "total_withdrawals": self.total_withdrawals,
            "total_accounting_pnl": total_accounting_pnl,
            "total_component_pnl": total_component_pnl,
            "core_realized_pnl": core_realized,
            "core_unrealized_pnl": core_unrealized,
            "tactical_realized_pnl": tact_realized,
            "tactical_unrealized_pnl": tact_unrealized,
            "covered_call_realized_pnl": opt_realized,
            "covered_call_unrealized_pnl": opt_unrealized,
            "financing_interest_paid": self.financing_interest_paid,
            "commissions_paid": self.commissions_paid,
            "slippage_paid": self.slippage_paid,
            "discrepancy": discrepancy,
            "reconciles": discrepancy < 1e-4,
        }
