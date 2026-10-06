"""Covered-call lifecycle state machine and cash accounting.

The ledger is intentionally isolated from portfolio execution. It provides
deterministic, auditable transitions that a later V2-D integration can compose
with V2-C without changing the underlying strategy.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from tactical_engine.options.contracts import (
    CoveredCallRecord,
    OptionContractType,
    OptionLifecycleState,
    OptionQuote,
)


class CoveredCallTransition(BaseModel, frozen=True):
    state_before: OptionLifecycleState
    state_after: OptionLifecycleState
    timestamp: datetime
    cash_delta: float
    realized_option_pnl: float
    shares_delivered: float = 0.0
    reason: str = ""


class CoveredCallLifecycle(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    state: OptionLifecycleState = OptionLifecycleState.AVAILABLE
    history: tuple[OptionLifecycleState, ...] = (OptionLifecycleState.AVAILABLE,)

    contract_symbol: str | None = None
    underlying: str | None = None
    strike: float | None = None
    expiration: datetime | None = None
    contracts: int = 0
    contract_multiplier: int = 100
    covered_shares: float = 0.0

    entry_time: datetime | None = None
    entry_premium: float = 0.0
    entry_fees: float = 0.0
    underlying_price_at_entry: float | None = None

    exit_time: datetime | None = None
    exit_premium: float = 0.0
    exit_fees: float = 0.0
    realized_option_pnl: float | None = None
    shares_delivered: float = 0.0

    @computed_field
    @property
    def notional_shares(self) -> float:
        return float(self.contracts * self.contract_multiplier)

    def _append_state(self, state: OptionLifecycleState) -> None:
        self.history = (*self.history, state)
        self.state = state

    def sell(
        self,
        quote: OptionQuote,
        *,
        contracts: int,
        eligible_underlying_shares: float,
        entry_fee: float = 0.0,
    ) -> CoveredCallTransition:
        if self.state != OptionLifecycleState.AVAILABLE:
            raise ValueError(f"Cannot sell a covered call from state {self.state}")
        if quote.contract_type != OptionContractType.CALL:
            raise ValueError("Covered-call lifecycle only accepts call contracts")
        if contracts <= 0:
            raise ValueError("Covered-call contracts must be positive")
        if quote.bid <= 0:
            raise ValueError("Covered-call sale requires a positive executable bid")
        if contracts * quote.contract_multiplier > eligible_underlying_shares:
            raise ValueError(
                "Covered-call write exceeds eligible underlying shares: "
                f"{contracts * quote.contract_multiplier} > {eligible_underlying_shares}"
            )
        if entry_fee < 0:
            raise ValueError("Entry fee cannot be negative")

        self.contract_symbol = quote.symbol
        self.underlying = quote.underlying
        self.strike = quote.strike
        self.expiration = quote.expiration
        self.contracts = contracts
        self.contract_multiplier = quote.contract_multiplier
        self.covered_shares = float(contracts * quote.contract_multiplier)
        self.entry_time = quote.timestamp
        self.entry_premium = quote.bid
        self.entry_fees = entry_fee
        self.underlying_price_at_entry = quote.underlying_price

        self._append_state(OptionLifecycleState.SOLD)
        self._append_state(OptionLifecycleState.OPEN)

        cash_delta = quote.bid * self.covered_shares - entry_fee
        return CoveredCallTransition(
            state_before=OptionLifecycleState.AVAILABLE,
            state_after=OptionLifecycleState.OPEN,
            timestamp=quote.timestamp,
            cash_delta=cash_delta,
            realized_option_pnl=0.0,
            reason="covered_call_sold_at_bid",
        )

    def buy_back(
        self,
        quote: OptionQuote,
        *,
        exit_fee: float = 0.0,
    ) -> CoveredCallTransition:
        if self.state != OptionLifecycleState.OPEN:
            raise ValueError(f"Cannot buy back a covered call from state {self.state}")
        if quote.symbol != self.contract_symbol:
            raise ValueError("Buyback quote does not match the open contract")
        if self.entry_time is None or quote.timestamp < self.entry_time:
            raise ValueError("Buyback quote cannot precede the sale timestamp")
        if quote.ask <= 0:
            raise ValueError("Covered-call buyback requires a positive executable ask")
        if exit_fee < 0:
            raise ValueError("Exit fee cannot be negative")

        self.exit_time = quote.timestamp
        self.exit_premium = quote.ask
        self.exit_fees = exit_fee
        self.realized_option_pnl = round(
            (self.entry_premium - quote.ask) * self.covered_shares
            - self.entry_fees
            - exit_fee,
            10,
        )
        self._append_state(OptionLifecycleState.BOUGHT_BACK)

        cash_delta = -(quote.ask * self.covered_shares) - exit_fee
        return CoveredCallTransition(
            state_before=OptionLifecycleState.OPEN,
            state_after=OptionLifecycleState.BOUGHT_BACK,
            timestamp=quote.timestamp,
            cash_delta=cash_delta,
            realized_option_pnl=self.realized_option_pnl,
            reason="covered_call_bought_back_at_ask",
        )

    def settle_expiration(
        self,
        *,
        settlement_time: datetime,
        underlying_close: float,
        assignment_fee: float = 0.0,
    ) -> CoveredCallTransition:
        if self.state != OptionLifecycleState.OPEN:
            raise ValueError(f"Cannot settle expiration from state {self.state}")
        if self.expiration is None or settlement_time < self.expiration:
            raise ValueError("Expiration settlement cannot occur before contract expiration")
        if underlying_close <= 0:
            raise ValueError("Underlying expiration price must be positive")
        if self.strike is None:
            raise ValueError("Open covered call is missing strike")
        if assignment_fee < 0:
            raise ValueError("Assignment fee cannot be negative")

        self.exit_time = settlement_time
        self.exit_premium = 0.0
        self.exit_fees = assignment_fee

        if underlying_close > self.strike:
            self.shares_delivered = self.covered_shares
            self.realized_option_pnl = round(
                self.entry_premium * self.covered_shares
                - self.entry_fees
                - assignment_fee,
                10,
            )
            self._append_state(OptionLifecycleState.ASSIGNED)
            cash_delta = self.strike * self.covered_shares - assignment_fee
            return CoveredCallTransition(
                state_before=OptionLifecycleState.OPEN,
                state_after=OptionLifecycleState.ASSIGNED,
                timestamp=settlement_time,
                cash_delta=cash_delta,
                realized_option_pnl=self.realized_option_pnl,
                shares_delivered=self.shares_delivered,
                reason="expiration_assignment",
            )

        self.shares_delivered = 0.0
        self.realized_option_pnl = round(
            self.entry_premium * self.covered_shares
            - self.entry_fees
            - assignment_fee,
            10,
        )
        self._append_state(OptionLifecycleState.EXPIRED)
        return CoveredCallTransition(
            state_before=OptionLifecycleState.OPEN,
            state_after=OptionLifecycleState.EXPIRED,
            timestamp=settlement_time,
            cash_delta=-assignment_fee,
            realized_option_pnl=self.realized_option_pnl,
            reason="expiration_without_assignment",
        )

    def to_record(self) -> CoveredCallRecord:
        if self.state == OptionLifecycleState.AVAILABLE:
            raise ValueError("Cannot serialize an unsold covered call")
        if not all(
            value is not None
            for value in (
                self.contract_symbol,
                self.underlying,
                self.strike,
                self.expiration,
                self.entry_time,
            )
        ):
            raise ValueError("Covered-call lifecycle is missing entry contract metadata")

        return CoveredCallRecord(
            contract_symbol=self.contract_symbol,
            underlying=self.underlying,
            strike=self.strike,
            expiration=self.expiration,
            entry_time=self.entry_time,
            exit_time=self.exit_time,
            entry_premium=self.entry_premium,
            exit_premium=self.exit_premium,
            contracts=self.contracts,
            realized_pnl=self.realized_option_pnl,
            was_assigned=self.state == OptionLifecycleState.ASSIGNED,
            underlying_shares_delivered=self.shares_delivered,
            status=self.state,
            entry_fees=self.entry_fees,
            exit_fees=self.exit_fees,
        )


def validate_covered_share_capacity(
    *,
    contracts: int,
    eligible_underlying_shares: float,
    contract_multiplier: int = 100,
) -> None:
    if contracts <= 0:
        raise ValueError("Covered-call contracts must be positive")
    if eligible_underlying_shares < 0:
        raise ValueError("Eligible underlying shares cannot be negative")
    required_shares = contracts * contract_multiplier
    if required_shares > eligible_underlying_shares:
        raise ValueError(
            f"Covered-call write would be under-covered: {required_shares} shares "
            f"required, {eligible_underlying_shares} eligible"
        )
