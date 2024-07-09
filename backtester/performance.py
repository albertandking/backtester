import numpy as np
import pandas as pd


def calculate_sharpe_ratio(returns, periods=252):
    if np.std(returns) == 0:
        return np.nan
    return (np.sqrt(periods) * np.mean(returns)) / np.std(returns)


def calculate_drawdowns(equity_curve):
    hwm = [0]
    eq_index = equity_curve.index
    drawdown = pd.Series(index=eq_index)
    duration = pd.Series(index=eq_index)

    for i in range(1, len(eq_index)):
        current_hwm = max(hwm[i - 1], equity_curve.iloc[i])
        hwm.append(current_hwm)
        drawdown.iloc[i] = hwm[i] - equity_curve.iloc[i]
        duration.iloc[i] = 0 if drawdown.iloc[i] == 0 else duration.iloc[i - 1] + 1

    return drawdown.max(), duration.max()
