import queue
from queue import Queue

import pandas as pd

from backtester.data import DataHandler
from backtester.event import EventType
from backtester.execution import ExecutionHandler
from backtester.portfolio import Portfolio
from backtester.strategy import Strategy


def backtest(
    events: Queue,
    data: DataHandler,
    portfolio: Portfolio,
    strategy: Strategy,
    broker: ExecutionHandler
) -> pd.DataFrame:
    while True:
        data.update_latest_data()
        if not data.continue_backtest:
            break

        while True:
            try:
                event = events.get(block=False)
            except queue.Empty:
                break

            if event is not None:
                if event.type == EventType.MARKET:
                    strategy.calculate_signals(event)
                    portfolio.update_time_index(event)
                elif event.type == EventType.SIGNAL:
                    portfolio.update_signal(event)
                elif event.type == EventType.ORDER:
                    broker.execute_order(event)
                elif event.type == EventType.FILL:
                    portfolio.update_fill(event)

    stats = portfolio.summary_stats()
    print(stats)
    temp_df = portfolio.create_equity_curve_dataframe()

    # portfolio.plot_all()
    return temp_df
