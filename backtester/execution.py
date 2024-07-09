from abc import ABC, abstractmethod
from datetime import datetime

from backtester.event import FillEvent, EventType


class ExecutionHandler(ABC):
    @abstractmethod
    def execute_order(self, event):
        pass


class SimulateExecutionHandler(ExecutionHandler):
    def __init__(self, events, verbose=False):
        self.events = events
        self.verbose = verbose

    def execute_order(self, event):
        if event.type == EventType.ORDER:
            if self.verbose:
                print("Order Executed:", event.symbol, event.quantity, event.direction)
            fill_event = FillEvent(datetime.utcnow(), event.symbol, 'ARCA', event.quantity, event.direction, 0)
            self.events.put(fill_event)
