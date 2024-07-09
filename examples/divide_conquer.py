import math

import pandas as pd

from backtester.event import SignalEvent, SignalType, EventType
from backtester.strategy import Strategy


class DivideAndConquerStrategy(Strategy):
    def __init__(self, data, portfolio):
        self.data = data
        self.symbol_list = self.data.symbol_list
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
                            self.put_event(signal)
                            print("Long:", data[-1][self.data.time_col], latest_close)
                    else:
                        quantity = math.floor(self.portfolio.current_positions[symbol] / 2)
                        if quantity != 0:
                            signal = SignalEvent(symbol, data[-1][self.data.time_col], SignalType.SHORT, quantity)
                            self.put_event(signal)
                            print("Exit:", data[-1][self.data.time_col], latest_close)


if __name__ == '__main__':
    from backtester.data import AKShareDataHandler
    from backtester.portfolio import NaivePortfolio
    from backtester.execution import SimulateExecutionHandler
    from backtester.core import backtest

    start_date = '20200101'  # 设置回测开始日期
    end_date = '20210201'  # 设置回测结束日期
    my_data = AKShareDataHandler(symbol_list=['000001'], start_date=start_date, end_date=end_date)
    my_portfolio = NaivePortfolio(data=my_data, strategy_name='king', initial_capital=2000000)
    my_strategy = DivideAndConquerStrategy(data=my_data, portfolio=my_portfolio)
    my_portfolio.strategy_name = my_strategy.name
    my_broker = SimulateExecutionHandler()
    df = backtest(my_data, my_portfolio, my_strategy, my_broker)
