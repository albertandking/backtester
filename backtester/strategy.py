from abc import ABC, abstractmethod


class Strategy(ABC):
    @abstractmethod
    def calculate_signals(self, event):
        pass

    def plot(self):
        pass
