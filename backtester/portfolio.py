from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import style

from backtester.event import EventType, SignalType, OrderType, OrderDirection, OrderEvent
from backtester.performance import calculate_sharpe_ratio, calculate_drawdowns
from backtester.event_manager import EventManager


class Portfolio(ABC):
    @abstractmethod
    def update_signal(self, event):
        pass

    @abstractmethod
    def update_fill(self, event):
        pass

    @abstractmethod
    def update_time_index(self, event):
        pass

    @abstractmethod
    def summary_stats(self):
        pass

    @abstractmethod
    def plot_all(self):
        pass

    @abstractmethod
    def create_equity_curve_dataframe(self):
        pass


class NaivePortfolio(Portfolio):
    def __init__(self, data, strategy_name, initial_capital=1.0):
        self.data = data
        self.symbol_list = self.data.symbol_list
        self.initial_capital = initial_capital
        self.strategy_name = strategy_name
        self.all_positions = []
        self.current_positions = {symbol: 0.0 for symbol in self.symbol_list}
        self.all_holdings = []
        self.current_holdings = self.construct_current_holdings()
        self.equity_curve = pd.DataFrame()
        self.holdings_curve = pd.DataFrame()

    def construct_current_holdings(self):
        holdings = {symbol: 0.0 for symbol in self.symbol_list}
        holdings['cash'] = self.initial_capital
        holdings['commission'] = 0.0
        holdings['total'] = self.initial_capital
        return holdings

    def update_time_index(self, event):
        latest_datetime = None
        for symbol in self.symbol_list:
            latest_data = self.data.get_latest_data(symbol, num=1)
            if latest_data:
                latest_datetime = latest_data[0]['date']
                break

        if latest_datetime is None:
            return

        positions = {symbol: self.current_positions[symbol] for symbol in self.symbol_list}
        positions['datetime'] = latest_datetime
        self.all_positions.append(positions)

        holdings = {symbol: 0.0 for symbol in self.symbol_list}
        holdings['datetime'] = latest_datetime
        holdings['cash'] = self.current_holdings['cash']
        holdings['commission'] = self.current_holdings['commission']
        holdings['total'] = self.current_holdings['cash']

        for symbol in self.symbol_list:
            latest_data = self.data.get_latest_data(symbol, num=1)
            if latest_data:
                market_value = self.current_positions[symbol] * latest_data[0]['close']
                holdings[symbol] = market_value
                holdings['total'] += market_value

        self.all_holdings.append(holdings)

    def update_positions_from_fill(self, fill):
        fill_dir = 1 if fill.direction == OrderDirection.BUY else -1
        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_fill(self, fill):
        fill_dir = 1 if fill.direction == OrderDirection.BUY else -1
        latest_data = self.data.get_latest_data(fill.symbol, num=1)
        if latest_data:
            fill_cost = latest_data[0]['close']
            cost = fill_cost * fill_dir * fill.quantity
            self.current_holdings[fill.symbol] += cost
            self.current_holdings['commission'] += fill.commission
            self.current_holdings['cash'] -= (cost + fill.commission)
            self.current_holdings['total'] -= (cost + fill.commission)

    def update_fill(self, event):
        if event.type == EventType.FILL:
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_naive_order(self, signal):
        order = None
        symbol = signal.symbol
        direction = signal.signal_type
        quantity = signal.quantity
        order_type = OrderType.MARKET

        if direction == SignalType.LONG:
            order = OrderEvent(symbol, order_type, quantity, OrderDirection.BUY)
        elif direction == SignalType.SHORT:
            order = OrderEvent(symbol, order_type, quantity, OrderDirection.SELL)
        elif direction == SignalType.EXIT:
            current_quantity = self.current_positions[symbol]
            if current_quantity > 0:
                order = OrderEvent(symbol, order_type, abs(int(current_quantity)), OrderDirection.SELL)
            elif current_quantity < 0:
                order = OrderEvent(symbol, order_type, abs(int(current_quantity)), OrderDirection.BUY)

        return order

    def update_signal(self, event):
        if event.type == EventType.SIGNAL:
            order_event = self.generate_naive_order(event)
            EventManager().put(order_event)

    def create_equity_curve_dataframe(self):
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index(keys='datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve
        self.holdings_curve = curve['total']
        return curve

    def summary_stats(self) -> pd.DataFrame:
        self.create_equity_curve_dataframe()
        total_return = self.equity_curve['equity_curve'].iloc[-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = calculate_sharpe_ratio(returns)
        max_dd, dd_duration = calculate_drawdowns(pnl)

        stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),
                 ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
                 ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
                 ("Drawdown Duration", "%d" % dd_duration)]

        temp_df = pd.DataFrame(stats, columns=['item', 'value'])
        return temp_df

    def curve_df(self):
        return self.equity_curve

    def plot_holdings(self):
        holdings_fig, holdings_ax = plt.subplots()
        self.holdings_curve.plot(ax=holdings_ax)
        holdings_ax.set_title('Holdings')
        holdings_ax.set_xlabel('Time')
        holdings_ax.set_ylabel('Total')

    def plot_performance(self):
        performance_df = self.data.create_baseline_dataframe()
        performance_df[self.strategy_name] = self.equity_curve['equity_curve']
        performance_df = (performance_df * 100) - 100
        performance_fig, performance_ax = plt.subplots()
        performance_df.plot(ax=performance_ax)
        performance_ax.set_title('Performance')
        performance_ax.set_xlabel('Time')
        performance_ax.set_ylabel('Return (%)')

    def plot_all(self):
        style.use('ggplot')
        self.create_equity_curve_dataframe()
        self.plot_holdings()
        self.plot_performance()
        plt.show()
