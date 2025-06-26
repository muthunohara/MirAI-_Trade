"""
premium_temp_fetcher.py
-----------------------
プレミアム 4 API を 1 本で呼ぶ暫定版。
signature / logging / エラーハンドリング は既存 fetcher と同一。
"""
from typing import Dict
import requests, pandas as pd
from logging import Logger
from app.core.config import AppConfig

# ---------- 個別 API 呼び出し (内部関数) ----------
def _call(cfg: AppConfig, id_tok: str, lg: Logger,
          url_key: str, params: Dict[str, str]) -> pd.DataFrame:
    url = getattr(cfg.jquants.endpoints, url_key)
    headers = {"Authorization": f"Bearer {id_tok}"}
    lg.info(f"{url_key} 取得: {url}  params={params}")
    r = requests.get(url, headers=headers, params=params, timeout=10)
    if r.status_code != 200:
        lg.error(f"{url_key} 失敗 {r.status_code}: {r.text[:120]}")
        raise RuntimeError(f"{url_key} API error")
    return pd.DataFrame(r.json().get(url_key, []))

# ---------- 公開関数 ----------
def fetch_premium_temp(cfg: AppConfig, id_tok: str,
                       lg: Logger, target_date: str) -> Dict[str, pd.DataFrame]:
    """プレミアム4 API を辞書で返す（キー名＝API 名）"""
    return {
        "futures" : _call(cfg, id_tok, lg,
                          "futures_prices", {"date": target_date}),
        "margin"  : _call(cfg, id_tok, lg,
                          "weekly_margin_interest", {"date": target_date}),
        "short"   : _call(cfg, id_tok, lg,
                          "short_selling_positions", {"calculated_date": target_date}),
        "trades"  : _call(cfg, id_tok, lg,
                          "trades_spec", {"date": target_date}),
    }
