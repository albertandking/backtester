from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class EventType(Enum):
    MARKET = auto()
    SIGNAL = auto()
    ORDER = auto()
    FILL = auto()


class SignalType(Enum):
    LONG = auto()
    SHORT = auto()
    EXIT = auto()


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()


class OrderDirection(Enum):
    BUY = auto()
    SELL = auto()


class Event(ABC):
    type: EventType


@dataclass
class MarketEvent(Event):
    type: EventType = EventType.MARKET


@dataclass
class SignalEvent(Event):
    symbol: str
    datetime: datetime
    signal_type: SignalType
    quantity: int
    type: EventType = EventType.SIGNAL


@dataclass
class OrderEvent(Event):
    symbol: str
    order_type: OrderType
    quantity: int
    direction: OrderDirection
    type: EventType = EventType.ORDER

    def print_order(self):
        print(
            f"Order: Symbol={self.symbol}, Type={self.order_type.name}, "
            f"Quantity={self.quantity}, Direction={self.direction.name}"
        )


@dataclass
class FillEvent(Event):
    time_index: datetime
    symbol: str
    exchange: str
    quantity: int
    direction: OrderDirection
    fill_cost: float
    commission: Optional[float] = None
    type: EventType = EventType.FILL

    def __post_init__(self):
        if self.commission is None:
            self.commission = self.calculate_ib_commission()

    def calculate_ib_commission(self) -> float:
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else:
            full_cost = max(1.3, 0.008 * self.quantity)
        return min(full_cost, 0.005 * self.quantity * self.fill_cost)
