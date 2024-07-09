import math

import pandas as pd

from backtester.event import SignalEvent, SignalType, EventType
from backtester.strategy import Strategy


class DivideAndConquerStrategy(Strategy):
    def __init__(self, data, events, portfolio):
        self.data = data
        self.symbol_list = self.data.symbol_list
        self.events = events
        self.portfolio = portfolio
        self.name = 'Divide And Conquer'

    def calculate_signals(self, event):
        if event.type == EventType.MARKET:
            for symbol in self.symbol_list:
                data = self.data.get_latest_data(symbol, num=7)
                temp_df = pd.DataFrame(data, columns=['symbol', 'date', 'close'])
                temp_df = temp_df.drop(labels=['symbol'], axis=1)
                temp_df.set_index(keys='date', inplace=True)
                if data is not None and len(data) > 0:
                    mean = temp_df['close'].pct_change().mean()
                    latest_close = data[-1][self.data.price_col]
                    if mean < 0:
                        quantity = math.floor(self.portfolio.current_holdings['cash'] / (2 * latest_close))
                        if quantity != 0:
                            signal = SignalEvent(symbol, data[-1][self.data.time_col], SignalType.LONG, quantity)
                            self.events.put(signal)
                            print("Long:", data[-1][self.data.time_col], latest_close)
                    else:
                        quantity = math.floor(self.portfolio.current_positions[symbol] / 2)
                        if quantity != 0:
                            signal = SignalEvent(symbol, data[-1][self.data.time_col], SignalType.SHORT, quantity)
                            self.events.put(signal)
                            print("Exit:", data[-1][self.data.time_col], latest_close)


if __name__ == '__main__':
    import queue
    from backtester.data import HistoricDataHandler
    from backtester.portfolio import NaivePortfolio
    from backtester.execution import SimulateExecutionHandler
    from backtester.core import backtest

    my_events = queue.Queue()
    start_date = '20200101'  # 设置回测开始日期
    end_date = '20210201'  # 设置回测结束日期
    my_data = HistoricDataHandler(events=my_events, symbol_list=['000001'], start_date=start_date, end_date=end_date)
    my_portfolio = NaivePortfolio(data=my_data, events=my_events, strategy_name='king', initial_capital=2000000)
    my_strategy = DivideAndConquerStrategy(data=my_data, events=my_events, portfolio=my_portfolio)
    my_portfolio.strategy_name = my_strategy.name
    my_broker = SimulateExecutionHandler(my_events)

    df = backtest(my_events, my_data, my_portfolio, my_strategy, my_broker)
