from typing import Optional
import requests
import pandas as pd
from logging import Logger
from app.core.config import AppConfig
from datetime import datetime

def fetch_daily_quotes(
    config: AppConfig,
    id_token: str,
    logger: Logger,
    target_date: str
) -> pd.DataFrame:
    """
    指定した日付の株価四本値を取得する。
    """
    url = config.jquants.endpoints.daily_quotes
    headers = {"Authorization": f"Bearer {id_token}"}
    params = {"date": target_date}

    logger.info(f"株価四本値取得: {url} パラメータ: {params}")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        logger.error(f"株価四本値取得失敗: {response.status_code} {response.text}")
        raise RuntimeError("株価四本値API呼び出しに失敗")

    records = response.json().get("daily_quotes", [])
    logger.info(f"{target_date} のデータ件数: {len(records)}")

    df = pd.DataFrame(records)

    # 日付型変換（JOIN対応のため）
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date

    return df
