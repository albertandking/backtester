import math

from backtester.event import SignalEvent, SignalType, EventType
from backtester.strategy import Strategy


class BuyAndHoldStrategy(Strategy):
    def __init__(self, data, events, portfolio):
        self.data = data
        self.symbol_list = self.data.symbol_list
        self.events = events
        self.portfolio = portfolio
        self.name = 'Buy and Hold'

        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        bought = {}
        for symbol in self.symbol_list:
            bought[symbol] = False

        return bought

    def calculate_signals(self, event):
        if event.type == EventType.MARKET:
            for symbol in self.symbol_list:
                data = self.data.get_latest_data(symbol, num=1)
                if data is not None and len(data) > 0:
                    if self.bought[symbol] is False:
                        quantity = math.floor(self.portfolio.current_holdings['cash'] / data[-1][self.data.price_col])
                        signal = SignalEvent(symbol, data[0][self.data.time_col], SignalType.LONG, quantity)
                        self.events.put(signal)
                        self.bought[symbol] = True


class SellAndHoldStrategy(Strategy):
    def __init__(self, data, events, portfolio):
        self.data = data
        self.symbol_list = self.data.symbol_list
        self.events = events
        self.portfolio = portfolio
        self.name = 'Sell and Hold'

        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        bought = {}
        for symbol in self.symbol_list:
            bought[symbol] = False

        return bought

    def calculate_signals(self, event):
        if event.type == EventType.MARKET:
            for symbol in self.symbol_list:
                data = self.data.get_latest_data(symbol)
                if data is not None and len(data) > 0:
                    if self.bought[symbol] is False:
                        quantity = math.floor(self.portfolio.current_holdings['cash'] / data[-1][self.data.price_col])
                        signal = SignalEvent(symbol, data[0][self.data.time_col], SignalType.SHORT, quantity)
                        self.events.put(signal)
                        self.bought[symbol] = True


if __name__ == '__main__':
    import queue
    from backtester.data import AKShareDataHandler
    from backtester.portfolio import NaivePortfolio
    from backtester.execution import SimulateExecutionHandler
    from backtester.core import backtest

    my_events = queue.Queue()
    start_date = '20200101'  # 设置回测开始日期
    end_date = '20210201'  # 设置回测结束日期
    my_data = AKShareDataHandler(events=my_events, symbol_list=['000001'], start_date=start_date, end_date=end_date)
    my_portfolio = NaivePortfolio(data=my_data, events=my_events, strategy_name='king', initial_capital=2000000)
    # my_strategy = BuyAndHoldStrategy(data=my_data, events=my_events, portfolio=my_portfolio)
    my_strategy = SellAndHoldStrategy(data=my_data, events=my_events, portfolio=my_portfolio)
    my_portfolio.strategy_name = my_strategy.name
    my_broker = SimulateExecutionHandler(my_events)

    df = backtest(my_events, my_data, my_portfolio, my_strategy, my_broker)
