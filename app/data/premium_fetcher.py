"""
プレミアム４ API 一括フェッチャ
・先物四本値         (/derivatives/futures)
・信用取引週末残高   (/markets/weekly_margin_interest)
・空売り残高報告     (/markets/short_selling_positions)
・投資部門別売買情報 (/markets/trades_spec)

使い方（例）
    from app.data.premium_fetcher import get_premium_data
    dfs = get_premium_data(id_token, logger, "2025-06-25")
"""

from __future__ import annotations
from typing import Dict, Any
import requests, pandas as pd
from logging import Logger
from app.core.config import config as cfg   # ❷ alias cfg

# ---------------- 共通 GET ----------------
def _get(url: str, headers: Dict[str, str], params: Dict[str, Any], lg: Logger):
    lg.debug(f"GET {url}  params={params}")
    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

# -------- 個別 API ラッパ --------
def _futures(id_token: str, lg: Logger, dt: str) -> pd.DataFrame:
    url = cfg.jquants.endpoints.futures_prices
    js  = _get(url, {"Authorization": f"Bearer {id_token}"}, {"date": dt}, lg)
    df  = pd.DataFrame(js.get("futures_prices", []))
    if not df.empty:
        df = df[["Date", "SettlementPrice", "Volume"]]
    return df

def _margin(id_token: str, lg: Logger, dt: str) -> pd.DataFrame:
    url = cfg.jquants.endpoints.weekly_margin_interest
    js  = _get(url, {"Authorization": f"Bearer {id_token}"}, {"date": dt}, lg)
    return pd.DataFrame(js.get("weekly_margin_interest", []))

def _short(id_token: str, lg: Logger, dt: str) -> pd.DataFrame:
    url = cfg.jquants.endpoints.short_selling_positions
    js  = _get(url, {"Authorization": f"Bearer {id_token}"}, {"date": dt}, lg)
    return pd.DataFrame(js.get("short_selling_positions", []))

def _trades(id_token: str, lg: Logger, dt: str) -> pd.DataFrame:
    url = cfg.jquants.endpoints.trades_spec
    js  = _get(url, {"Authorization": f"Bearer {id_token}"}, {"date": dt}, lg)
    return pd.DataFrame(js.get("trades_spec", []))

# -------------- 公開関数 --------------
def get_premium_data(id_token: str, logger: Logger, target_date: str
                     ) -> Dict[str, pd.DataFrame]:
    """
    target_date : 'YYYY-MM-DD'
    戻り値: {'futures': df, 'margin': df, 'short': df, 'trades': df}
    """
    return {
        "futures": _futures(id_token, logger, target_date),
        "margin" : _margin(id_token, logger, target_date),
        "short"  : _short(id_token, logger, target_date),
        "trades" : _trades(id_token, logger, target_date),
    }
