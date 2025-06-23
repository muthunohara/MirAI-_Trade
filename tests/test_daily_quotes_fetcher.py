from pathlib import Path
import pytest
import pandas as pd
from app.core.config import load_config
from app.core.logger import setup_logger
from app.data.jquants_signin import get_refresh_token, get_id_token
from app.data.trading_days_fetcher import get_latest_trading_days
from app.data.daily_quotes_fetcher import fetch_daily_quotes

# config.yaml の絶対パスを設定
CONFIG_PATH = Path(__file__).parent.parent / "configs" / "config.yaml"

# コンフィグ情報を読み込む fixture
@pytest.fixture(scope="module")
def config():
    return load_config(str(CONFIG_PATH))

# ロガーを初期化する fixture
@pytest.fixture(scope="module")
def logger(config):
    return setup_logger(config.logging)

# IDトークンを取得する fixture
@pytest.fixture(scope="module")
def id_token(config, logger):
    refresh_token = get_refresh_token(config, logger)
    return get_id_token(config, refresh_token, logger)

# fetch_daily_quotes のテスト
def test_fetch_daily_quotes(config, id_token, logger):
    try:
        # 直近6営業日を取得
        latest_days = get_latest_trading_days(config, id_token, logger, 6)

        # 各営業日について株価四本値を取得
        all_dataframes = []
        for date_str in latest_days:
            df = fetch_daily_quotes(config, id_token, logger, date_str)
            assert df is not None
            assert not df.empty
            all_dataframes.append(df)
            logger.info(f"{date_str} の株価四本値取得成功: {len(df)}件")

        # 全体の確認
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        assert not combined_df.empty
        logger.info(f"全6営業日分の株価四本値合計件数: {len(combined_df)}")

    except Exception as e:
        logger.error(f"株価四本値データ取得中に例外が発生しました: {e}")
        raise
