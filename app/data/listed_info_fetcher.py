import requests
import pandas as pd
from app.core.config import AppConfig
from logging import Logger


def fetch_listed_info(config: AppConfig, id_token: str, logger: Logger) -> pd.DataFrame:
    """
    J-Quants APIの上場銘柄一覧エンドポイントから最新の上場銘柄情報を取得する。

    Args:
        config (AppConfig): アプリケーション設定オブジェクト。
        id_token (str): J-Quants APIのIDトークン。
        logger (Logger): ロガーインスタンス。

    Returns:
        pd.DataFrame: 上場銘柄情報を含むDataFrame。
    """
    url = config.jquants.endpoints.listed_info
    headers = {"Authorization": f"Bearer {id_token}"}

    logger.info(f"上場銘柄一覧取得: {url}")
    response = requests.get(url, headers=headers)
    logger.debug(f"Status Code: {response.status_code}")
    logger.debug(f"Response Preview: {response.text[:300]}")

    if response.status_code != 200:
        raise RuntimeError(f"上場銘柄一覧の取得に失敗しました: {response.status_code} {response.text}")

    data = response.json().get("info", [])
    df = pd.DataFrame(data)
    logger.info(f"上場銘柄一覧の取得成功: {len(df)}件")
    return df
