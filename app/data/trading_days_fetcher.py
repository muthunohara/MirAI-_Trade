import requests
from datetime import datetime
from app.core.config import AppConfig
from typing import List

def get_latest_trading_days(config: AppConfig, id_token: str, logger, days: int = 6) -> List[str]:
    """
    J-Quants APIを用いて、過去の営業日を取得。
    HolidayDivisionが "1" または "2" の日付のみを営業日として扱う。

    Args:
        config (AppConfig): 設定情報
        id_token (str): 認証トークン
        logger (Logger): ロガーインスタンス
        days (int): 取得する営業日数（デフォルト6）

    Returns:
        List[str]: 過去の営業日（YYYY-MM-DD形式の文字列）
    """
    url = config.jquants.endpoints.trading_calendar
    headers = {"Authorization": f"Bearer {id_token}"}

    logger.debug(f"GET {url}")
    response = requests.get(url, headers=headers)
    logger.debug(f"Status Code: {response.status_code}")
    logger.debug(f"Response Preview: {response.text[:300]}...")
    response.raise_for_status()

    data = response.json()
    all_days = [
        item["Date"] for item in data["trading_calendar"]
        if item["HolidayDivision"] in ["1", "2"]
    ]

    # datetimeに変換して本日以前に限定
    all_days_dt = sorted(datetime.strptime(d, "%Y-%m-%d").date() for d in all_days)
    today = datetime.today().date()
    past_days = [d for d in all_days_dt if d < today]

    latest_days = past_days[-days:]
    logger.info("取得した営業日（最新%d件）:" % days)
    for d in latest_days:
        logger.info("  %s (%s)" % (d.isoformat(), d.strftime("%A")))

    return [d.isoformat() for d in latest_days]
