from abc import ABC, abstractmethod
from datetime import datetime

from backtester.event import FillEvent, EventType
from backtester.event_manager import EventManager


class ExecutionHandler(ABC):
    @abstractmethod
    def execute_order(self, event):
        pass


class SimulateExecutionHandler(ExecutionHandler):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def execute_order(self, event):
        if event.type == EventType.ORDER:
            if self.verbose:
                print("Order Executed:", event.symbol, event.quantity, event.direction)
            fill_event = FillEvent(datetime.utcnow(), event.symbol, 'ARCA', event.quantity, event.direction, 0)
            EventManager().put(fill_event)
