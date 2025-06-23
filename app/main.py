from app.core.config import load_config
from app.core.logger import setup_logger
from app.data.jquants_signin import get_refresh_token, get_id_token
from app.data.trading_days_fetcher import get_latest_trading_days
from app.data.daily_quotes_fetcher import fetch_daily_quotes
from app.data.listed_info_fetcher import fetch_listed_info
from app.scoring.score_stocks import score_stocks
from app.exporters.export_scores_to_excel import export_scores_to_excel

import pandas as pd
import os

def main():
    """
    MirAI_Trade 初期リリース版のエントリーポイント。
    株価情報をJ-Quants APIから取得し、スコア計算・Excel出力を行う。
    """
    # 設定読み込みとロガー初期化
    config = load_config("configs/config.yaml")
    logger = setup_logger(config.logging)

    # 認証トークン取得
    refresh_token = get_refresh_token(config, logger)
    id_token = get_id_token(config, refresh_token, logger)

    # 最新営業日（過去6日）を取得
    trading_days = get_latest_trading_days(config, id_token, logger, days=6)

    # 株価データを日別に取得・結合
    all_quotes = []
    for date in trading_days:
        df = fetch_daily_quotes(config, id_token, logger, target_date=date)
        all_quotes.append(df)

    quotes_df = pd.concat(all_quotes, ignore_index=True)

    # 上場銘柄情報を取得
    info_df = fetch_listed_info(config, id_token, logger)

    # スコア計算
    result_df = score_stocks(quotes_df, info_df, logger)

    # Excel出力
    export_scores_to_excel(result_df, output_dir="exports", logger=logger)


if __name__ == "__main__":
    main()
