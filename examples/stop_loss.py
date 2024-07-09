import math

from backtester.event import SignalEvent, SignalType, EventType
from backtester.strategy import Strategy


class StopLossStrategy(Strategy):
    def __init__(self, data, events, portfolio, stop_loss_percentage):
        self.data = data
        self.symbol_list = self.data.symbol_list
        self.events = events
        self.portfolio = portfolio
        self.name = 'Stop Loss'

        self.bought = self._calculate_initial_bought()
        self.stop_loss_percentage = stop_loss_percentage
        self.stop_loss = self._set_initial_stop_loss()

    def _calculate_initial_bought(self):
        bought = {}
        for symbol in self.symbol_list:
            bought[symbol] = False

        return bought

    def _set_initial_stop_loss(self):
        stop_loss = {}
        for symbol in self.symbol_list:
            stop_loss[symbol] = self.stop_loss_percentage

        return stop_loss

    def calculate_signals(self, event):
        if event.type == EventType.MARKET:
            for symbol in self.symbol_list:
                data = self.data.get_latest_data(symbol)
                if data is not None and len(data) > 0:
                    latest_close = data[-1]['close']
                    if (self.bought[symbol] is False
                        and latest_close > self.stop_loss[
                            symbol] / self.stop_loss_percentage):
                        quantity = math.floor(self.portfolio.current_holdings['cash'] / latest_close)
                        signal = SignalEvent(symbol, data[-1]['date'], SignalType.LONG, quantity)
                        self.events.put(signal)
                        self.bought[symbol] = True
                        self.stop_loss[symbol] = self.stop_loss_percentage * latest_close
                        print("Long:", data[-1]['date'], latest_close)
                        print("Stop Loss:", self.stop_loss[symbol])
                    elif self.bought[symbol] is True:
                        if latest_close <= self.stop_loss[symbol]:
                            quantity = self.portfolio.current_positions[symbol]
                            signal = SignalEvent(symbol, data[-1]['date'], SignalType.EXIT, quantity)
                            self.events.put(signal)
                            self.bought[symbol] = False
                            print("Exit:", data[-1]['date'], latest_close)
                            print("Stop Loss:", self.stop_loss[symbol])
                        else:
                            data = self.data.get_latest_data(symbol, num=2)
                            if data is not None and len(data) > 1:
                                if (data[-1]['close'] > data[0][
                                    'close']
                                    and self.stop_loss_percentage * data[-1]['close'] > self.stop_loss[
                                        symbol]):
                                    self.stop_loss[symbol] = self.stop_loss_percentage * data[-1]['close']


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
    my_strategy = StopLossStrategy(data=my_data, events=my_events, portfolio=my_portfolio, stop_loss_percentage=0.95)
    my_portfolio.strategy_name = my_strategy.name
    my_broker = SimulateExecutionHandler(my_events)

    df = backtest(my_events, my_data, my_portfolio, my_strategy, my_broker)
