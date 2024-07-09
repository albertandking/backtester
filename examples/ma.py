import math

import pandas as pd

from backtester.event import SignalEvent, SignalType, EventType
from backtester.strategy import Strategy


class MAStrategy(Strategy):
    def __init__(self, data, portfolio, short_period, long_period, verbose=False):
        self.data = data
        self.symbol_list = self.data.symbol_list
        self.portfolio = portfolio
        self.short_period = short_period
        self.long_period = long_period
        self.name = 'Moving Averages Long'
        self.verbose = verbose

        self.signals = self._setup_signals()
        self.strategy = self._setup_strategy()
        self.bought = self._setup_initial_bought()

    def _setup_signals(self):
        signals = {}
        for symbol in self.symbol_list:
            signals[symbol] = pd.DataFrame(columns=['date', 'signal'])
        return signals

    def _setup_strategy(self):
        strategy = {}
        for symbol in self.symbol_list:
            strategy[symbol] = pd.DataFrame(columns=['date', 'short', 'long'])

        return strategy

    def _setup_initial_bought(self):
        bought = {}
        for symbol in self.symbol_list:
            bought[symbol] = False

        return bought

    def calculate_long_short(self, df):
        price_short = df['close'].ewm(span=self.short_period, min_periods=self.short_period, adjust=False).mean()
        price_long = df['close'].ewm(span=self.long_period, min_periods=self.long_period, adjust=False).mean()

        # 确保索引在有效范围内
        if len(price_short) > self.short_period:
            price_short = price_short.iloc[-1]
        else:
            price_short = price_short.iloc[-1]  # 或者其他默认值

        if len(price_long) > self.long_period:
            price_long = price_long.iloc[-1]
        else:
            price_long = price_long.iloc[-1]  # 或者其他默认值

        return price_short, price_long

    def calculate_signals(self, event):
        if event.type == EventType.MARKET:
            for symbol in self.symbol_list:
                data = self.data.get_latest_data(symbol, num=-1)
                temp_df = pd.DataFrame(data, columns=['symbol', 'date', 'close'])
                temp_df = temp_df.drop(labels=['symbol'], axis=1)
                temp_df.set_index(keys='date', inplace=True)
                if data is not None and len(data) >= self.long_period:
                    price_short, price_long = self.calculate_long_short(temp_df)
                    date = temp_df.index.values[-1]
                    price = temp_df['close'].iloc[-1]
                    self.signals[symbol] = pd.concat(
                        objs=[self.signals[symbol],
                              pd.DataFrame.from_dict(data={'date': date, "short": price_short, "long": price_long},
                                                     orient="index").T],
                        ignore_index=True)
                    if self.bought[symbol] is False and price_short > price_long:
                        quantity = math.floor(self.portfolio.current_holdings['cash'] / price)
                        signal = SignalEvent(symbol, date, SignalType.LONG, quantity)
                        self.put_event(signal)
                        self.bought[symbol] = True
                        self.signals[symbol] = pd.concat(
                            objs=[self.signals[symbol],
                                  pd.DataFrame.from_dict(data={'date': date, 'signal': quantity}, orient="index").T],
                            ignore_index=True)
                        if self.verbose:
                            print("long", date, price)
                    elif self.bought[symbol] is True and price_short < price_long:
                        quantity = self.portfolio.current_positions[symbol]
                        signal = SignalEvent(symbol, date, SignalType.EXIT, quantity)
                        self.put_event(signal)
                        self.bought[symbol] = False
                        self.signals[symbol] = pd.concat(
                            objs=[self.signals[symbol],
                                  pd.DataFrame.from_dict(data={'date': date, 'signal': -quantity}, orient="index").T],
                            ignore_index=True)
                        if self.verbose:
                            print("exit", date, price)


if __name__ == '__main__':
    from backtester.data import DataSource, DataLoader
    from backtester.portfolio import NaivePortfolio
    from backtester.execution import SimulateExecutionHandler
    from backtester.core import backtest

    symbol_list = ["000001"]
    start_date = '20200101'  # 设置回测开始日期
    end_date = '20210201'  # 设置回测结束日期
    data_loader = DataLoader(symbol_list=symbol_list, start_date=start_date, end_date=end_date,
                             source=DataSource.AKSHARE)
    my_portfolio = NaivePortfolio(data=data_loader(), strategy_name='king', initial_capital=2000000)
    my_strategy = MAStrategy(data=data_loader(), portfolio=my_portfolio, short_period=2, long_period=5,
                             verbose=True)
    my_broker = SimulateExecutionHandler()

    result_df = backtest(data=data_loader(), portfolio=my_portfolio, strategy=my_strategy, broker=my_broker)
    print(result_df)
