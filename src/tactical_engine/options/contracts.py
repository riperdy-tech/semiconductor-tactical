"""Deterministic option contract and quote models.

These models are intentionally provider-neutral. They represent executable
historical quote information; they do not synthesize option prices or Greeks.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, computed_field, model_validator


class OptionContractType(StrEnum):
    CALL = "CALL"
    PUT = "PUT"


class OptionLifecycleState(StrEnum):
    AVAILABLE = "AVAILABLE"
    SOLD = "SOLD"
    OPEN = "OPEN"
    BOUGHT_BACK = "BOUGHT_BACK"
    EXPIRED = "EXPIRED"
    ASSIGNED = "ASSIGNED"


class OptionQuote(BaseModel, frozen=True):
    symbol: str
    underlying: str
    timestamp: datetime
    contract_type: OptionContractType
    strike: float
    expiration: datetime
    bid: float
    ask: float
    underlying_price: float
    volume: float = 0.0
    open_interest: float = 0.0
    contract_multiplier: int = 100
    bid_size: float = 0.0
    ask_size: float = 0.0
    last: float | None = None
    quote_condition: str | None = None

    @model_validator(mode="after")
    def check_integrity(self) -> "OptionQuote":
        if self.timestamp.tzinfo is None or self.expiration.tzinfo is None:
            raise ValueError("Option quote and expiration timestamps must be timezone-aware")
        if self.expiration <= self.timestamp:
            raise ValueError("Option expiration must be after the quote timestamp")
        if not self.symbol.strip() or not self.underlying.strip():
            raise ValueError("Option symbol and underlying are required")
        if self.strike <= 0:
            raise ValueError("Option strike must be positive")
        if self.underlying_price <= 0:
            raise ValueError("Underlying price must be positive")
        if self.bid < 0 or self.ask < 0:
            raise ValueError("Option bid and ask prices cannot be negative")
        if self.ask < self.bid:
            raise ValueError(f"Ask ({self.ask}) cannot be less than bid ({self.bid})")
        if self.contract_multiplier <= 0:
            raise ValueError("Option contract multiplier must be positive")
        if self.volume < 0 or self.open_interest < 0:
            raise ValueError("Option volume and open interest cannot be negative")
        if self.bid_size < 0 or self.ask_size < 0:
            raise ValueError("Option bid and ask sizes cannot be negative")
        if self.last is not None and self.last < 0:
            raise ValueError("Option last price cannot be negative")
        return self

    @computed_field
    @property
    def mid(self) -> float:
        return round((self.bid + self.ask) / 2.0, 4)

    @computed_field
    @property
    def dte(self) -> int:
        delta = self.expiration - self.timestamp
        return max(0, int(delta.total_seconds() / 86400.0))

    @computed_field
    @property
    def is_executable_for_sale(self) -> bool:
        return self.bid > 0

    @computed_field
    @property
    def is_executable_for_buyback(self) -> bool:
        return self.ask > 0


class OptionPosition(BaseModel, frozen=True):
    symbol: str
    underlying: str
    contract_type: OptionContractType
    strike: float
    expiration: datetime
    quantity: float  # Negative for a short option position
    avg_price: float  # Executed premium per contract, not midpoint
    associated_underlying_shares: float = 0.0
    contract_multiplier: int = 100
    lifecycle_state: OptionLifecycleState = OptionLifecycleState.OPEN
    entry_time: datetime | None = None
    underlying_price_at_entry: float | None = None

    @model_validator(mode="after")
    def check_short_position(self) -> "OptionPosition":
        if self.quantity > 0:
            raise ValueError("OptionPosition quantity must be non-positive for the covered-call engine")
        if self.avg_price < 0:
            raise ValueError("OptionPosition average premium cannot be negative")
        if self.contract_multiplier <= 0:
            raise ValueError("Option contract multiplier must be positive")
        return self


class CoveredCallRecord(BaseModel, frozen=True):
    contract_symbol: str
    underlying: str
    strike: float
    expiration: datetime
    entry_time: datetime
    exit_time: datetime | None = None
    entry_premium: float
    exit_premium: float = 0.0
    contracts: int
    realized_pnl: float | None = None
    was_assigned: bool = False
    underlying_shares_delivered: float = 0.0
    status: OptionLifecycleState = OptionLifecycleState.OPEN
    entry_fees: float = 0.0
    exit_fees: float = 0.0
