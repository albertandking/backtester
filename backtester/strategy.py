from abc import ABC, abstractmethod

from backtester.event_manager import EventManager


class Strategy(ABC):
    @abstractmethod
    def calculate_signals(self, event):
        pass

    @staticmethod
    def put_event(event):
        EventManager().put(event)

    def plot(self):
        pass
