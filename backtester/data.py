from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Dict

import akshare as ak
import pandas as pd

from backtester.event import MarketEvent
from backtester.event_manager import EventManager


class DataSource(Enum):
    AKSHARE = auto()
    YFINANCE = auto()


class DataHandler(ABC):
    @abstractmethod
    def get_latest_data(self, symbol: str, num: int = 1) -> List[Dict]:
        pass

    @abstractmethod
    def update_latest_data(self) -> None:
        pass

    @property
    @abstractmethod
    def continue_backtest(self) -> bool:
        pass


class AKShareDataHandler(DataHandler):
    def __init__(self, symbol_list: List[str], start_date: str, end_date: str):
        self.symbol_list = symbol_list
        self.start_date = start_date
        self.end_date = end_date

        self.time_col = "date"
        self.price_col = "close"

        self.symbol_data: Dict[str, pd.DataFrame] = {}
        self.latest_symbol_data: Dict[str, List[Dict]] = {symbol: [] for symbol in symbol_list}
        self.all_data: Dict[str, pd.DataFrame] = {}  # 添加 all_data 属性
        self._continue_backtest = True  # 使用私有属性

        self._load_akshare_data()
        self._generators = {symbol: self._get_new_bar(symbol) for symbol in self.symbol_list}

    def _load_akshare_data(self):
        for symbol in self.symbol_list:
            data = ak.stock_zh_a_hist(symbol=symbol, start_date=self.start_date, end_date=self.end_date, adjust="hfq")
            data.set_index(keys='日期', inplace=True)
            data.index = pd.to_datetime(data.index)
            data = data[['收盘']]
            data.columns = ['close']
            self.symbol_data[symbol] = data[data['close'] > 0.0]
            self.all_data[symbol] = data  # 初始化 all_data

    def _get_new_bar(self, symbol: str):
        for index, row in self.symbol_data[symbol].iterrows():
            yield {"symbol": symbol, "date": index, "close": row["close"]}

    def get_latest_data(self, symbol: str, num: int = 1):
        try:
            return self.latest_symbol_data[symbol][-num:]
        except KeyError:
            print(f"{symbol} is not a valid symbol.")
            return []

    def update_latest_data(self):
        for symbol in self.symbol_list:
            try:
                bar = next(self._generators[symbol])
                # print(f"New bar for {symbol}: {bar}")  # 添加调试输出
                self.latest_symbol_data[symbol].append(bar)
            except StopIteration:
                self._continue_backtest = False
                # print(f"No more data for {symbol}. Stopping backtest.")  # 添加调试输出

        # self.events.put(MarketEvent())
        EventManager().put(MarketEvent())
        # print(f"Market event added. continue_backtest: {self.continue_backtest}")  # 添加调试输出

    @staticmethod
    def create_baseline_dataframe():
        # 假设基准是某个指数，例如上证指数
        baseline_symbol = 'sh000001'
        baseline_data = ak.stock_zh_index_daily(symbol=baseline_symbol)
        baseline_data.set_index(keys='date', inplace=True)
        baseline_data.index = pd.to_datetime(baseline_data.index)
        baseline_data = baseline_data[['close']]
        baseline_data.columns = ['Baseline']
        return baseline_data

    @property
    def continue_backtest(self) -> bool:
        return self._continue_backtest

    @continue_backtest.setter
    def continue_backtest(self, value: bool):
        self._continue_backtest = value


class DataLoader:
    def __init__(self, symbol_list: List[str], start_date: str, end_date: str, source: DataSource):
        self.symbol_list = symbol_list
        self.start_date = start_date
        self.end_date = end_date
        self.source = source
        self.data_handler = self._load_data_handler()

    def __call__(self) -> DataHandler:
        return self.data_handler

    def _load_data_handler(self) -> DataHandler:
        if self.source == DataSource.AKSHARE:
            return AKShareDataHandler(self.symbol_list, self.start_date, self.end_date)
        elif self.source == DataSource.YFINANCE:
            # 实现YahooDataHandler
            pass
        else:
            raise ValueError("Unsupported data source")
