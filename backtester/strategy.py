from abc import ABC, abstractmethod

from backtester.event_manager import EventManager


class Strategy(ABC):
    @abstractmethod
    def calculate_signals(self, event):
        pass

    def put_event(self, event):
        EventManager().put(event)

    def plot(self):
        pass
