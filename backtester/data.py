# 导入必要的模块
from abc import ABC, abstractmethod  # 用于创建抽象基类
from enum import Enum, auto  # 用于创建枚举类型
from typing import List, Dict  # 用于类型注解

import akshare as ak  # 导入akshare库用于获取股票数据
import pandas as pd  # 导入pandas用于数据处理

from backtester.event import MarketEvent  # 导入自定义的MarketEvent
from backtester.event_manager import EventManager  # 导入自定义的EventManager


# 定义数据源枚举类
class DataSource(Enum):
    AKSHARE = auto()
    YFINANCE = auto()


# 定义抽象基类DataHandler
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


# 实现AKShare数据处理类
class AKShareDataHandler(DataHandler):
    def __init__(self, symbol_list: List[str], start_date: str, end_date: str):
        self.symbol_list = symbol_list
        self.start_date = start_date
        self.end_date = end_date

        self.time_col = "date"
        self.price_col = "close"

        self.symbol_data: Dict[str, pd.DataFrame] = {}
        self.latest_symbol_data: Dict[str, List[Dict]] = {symbol: [] for symbol in symbol_list}
        self.all_data: Dict[str, pd.DataFrame] = {}  # 存储所有数据
        self._continue_backtest = True  # 控制回测是否继续的标志

        self._load_akshare_data()  # 加载数据
        self._generators = {symbol: self._get_new_bar(symbol) for symbol in self.symbol_list}  # 创建数据生成器

    def _load_akshare_data(self):
        # 从 AKShare 加载数据并进行预处理
        for symbol in self.symbol_list:
            data = ak.stock_zh_a_hist(symbol=symbol, start_date=self.start_date, end_date=self.end_date, adjust="hfq")
            data.set_index(keys='日期', inplace=True)
            data.index = pd.to_datetime(data.index)
            data = data[['收盘']]
            data.columns = ['close']
            self.symbol_data[symbol] = data[data['close'] > 0.0]
            self.all_data[symbol] = data

    def _get_new_bar(self, symbol: str):
        # 生成器函数，用于逐个返回数据条目
        for index, row in self.symbol_data[symbol].iterrows():
            yield {"symbol": symbol, "date": index, "close": row["close"]}

    def get_latest_data(self, symbol: str, num: int = 1):
        # 获取最新的数据
        try:
            return self.latest_symbol_data[symbol][-num:]
        except KeyError:
            print(f"{symbol} is not a valid symbol.")
            return []

    def update_latest_data(self):
        # 更新最新数据并触发市场事件
        for symbol in self.symbol_list:
            try:
                bar = next(self._generators[symbol])
                self.latest_symbol_data[symbol].append(bar)
            except StopIteration:
                self._continue_backtest = False

        EventManager().put(MarketEvent())

    @staticmethod
    def create_baseline_dataframe():
        # 创建基准数据框（例如，上证指数）
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


# 数据加载器类
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
        # 根据指定的数据源创建相应的DataHandler
        if self.source == DataSource.AKSHARE:
            return AKShareDataHandler(self.symbol_list, self.start_date, self.end_date)
        elif self.source == DataSource.YFINANCE:
            # 实现YahooDataHandler
            pass
        else:
            raise ValueError("Unsupported data source")
