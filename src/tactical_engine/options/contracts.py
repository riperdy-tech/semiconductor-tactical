from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, computed_field, model_validator


class OptionContractType(StrEnum):
    CALL = "CALL"
    PUT = "PUT"


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

    @model_validator(mode="after")
    def check_spread(self) -> "OptionQuote":
        if self.bid < 0 or self.ask < 0:
            raise ValueError("Option bid and ask prices cannot be negative")
        if self.ask < self.bid:
            raise ValueError(f"Ask ({self.ask}) cannot be less than bid ({self.bid})")
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


class OptionPosition(BaseModel, frozen=True):
    symbol: str
    underlying: str
    contract_type: OptionContractType
    strike: float
    expiration: datetime
    quantity: float  # Negative for short covered call
    avg_price: float
    associated_underlying_shares: float = 0.0


class CoveredCallRecord(BaseModel, frozen=True):
    contract_symbol: str
    underlying: str
    strike: float
    expiration: datetime
    entry_time: datetime
    exit_time: datetime
    entry_premium: float
    exit_premium: float
    contracts: float
    realized_pnl: float
    was_assigned: bool
    underlying_shares_delivered: float = 0.0
