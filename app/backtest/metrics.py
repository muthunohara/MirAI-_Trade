"""app/backtest/metrics.py
共通バックテスト指標ユーティリティ。

- 平均日次リターン µ
- 勝率
- 年次シャープレシオ
- 最大ドローダウン (DD)

単体で import して使用する。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 250

__all__ = [
    "calc_metrics",
]


def calc_metrics(ret_series: pd.Series) -> dict[str, float]:
    """リターン系列から主要評価指標を計算。

    Args:
        ret_series: 日次リターン (float) Series

    Returns:
        dict: {mu, win_rate, sharpe, max_dd}
    """
    mu = ret_series.mean()
    win_rate = (ret_series > 0).mean()
    sigma = ret_series.std(ddof=0)
    sharpe = (np.sqrt(TRADING_DAYS_PER_YEAR) * mu / sigma) if sigma != 0 else 0.0

    # 最大 DD
    cumulative = (1 + ret_series).cumprod()
    peak = cumulative.cummax()
    dd = (cumulative / peak - 1).min()

    return {
        "mu": round(mu, 4),
        "win_rate": round(win_rate, 4),
        "sharpe": round(sharpe, 4),
        "max_dd": round(dd, 4),
    }
