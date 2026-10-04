from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Bar(BaseModel, frozen=True):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    vwap: float | None = None
    provider: str = "synthetic"
    adjustment_status: str = "unadjusted"

    @model_validator(mode="after")
    def check_ohlc(self) -> "Bar":
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) cannot be less than low ({self.low})")
        if self.open < 0 or self.high < 0 or self.low < 0 or self.close < 0:
            raise ValueError("Prices cannot be negative")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        if not (self.low <= self.open <= self.high and self.low <= self.close <= self.high):
            raise ValueError("Open and Close must be within High and Low")
        return self


class Quote(BaseModel, frozen=True):
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    bid_size: float = 0.0
    ask_size: float = 0.0


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class SignalIntent(BaseModel, frozen=True):
    symbol: str
    timestamp: datetime
    action: Literal["ENTER_LONG", "EXIT_LONG", "HOLD"] = "HOLD"
    strength: float = 1.0
    reason: str = ""
    stop_price: float | None = None
    target_price: float | None = None


class Order(BaseModel, frozen=True):
    order_id: str
    symbol: str
    timestamp: datetime
    side: OrderSide
    order_type: OrderType
    quantity: float
    limit_price: float | None = None
    stop_price: float | None = None
    stop_loss_price: float | None = None
    target_price: float | None = None
    entry_atr: float | None = None
    tag: str = ""


class Fill(BaseModel, frozen=True):
    order_id: str
    symbol: str
    timestamp: datetime
    side: OrderSide
    quantity: float
    price: float
    reference_price: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0


class Position(BaseModel, frozen=True):
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0


class AccountState(BaseModel, frozen=True):
    timestamp: datetime
    cash: float
    positions: dict[str, Position] = Field(default_factory=dict)
    margin_debt: float = 0.0
    equity: float = 0.0
