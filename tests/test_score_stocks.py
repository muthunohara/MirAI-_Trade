from pathlib import Path
import pytest
import pandas as pd
from app.core.config import load_config
from app.core.logger import setup_logger
from app.data.jquants_signin import get_refresh_token, get_id_token
from app.data.trading_days_fetcher import get_latest_trading_days
from app.data.daily_quotes_fetcher import fetch_daily_quotes
from app.data.listed_info_fetcher import fetch_listed_info
from scoring.score_stocks import score_stocks

# config.yaml の絶対パスを設定
CONFIG_PATH = Path(__file__).parent.parent / "configs" / "config.yaml"

@pytest.fixture(scope="module")
def config():
    return load_config(str(CONFIG_PATH))

@pytest.fixture(scope="module")
def logger(config):
    return setup_logger(config.logging)

@pytest.fixture(scope="module")
def id_token(config, logger):
    refresh_token = get_refresh_token(config, logger)
    return get_id_token(config, refresh_token, logger)

def test_score_stocks(config, id_token, logger):
    try:
        # 株価データを6営業日分取得
        trading_days = get_latest_trading_days(config, id_token, logger, 6)
        all_quotes = []
        for date in trading_days:
            df = fetch_daily_quotes(config, id_token, logger, date)
            all_quotes.append(df)
        quotes_df = pd.concat(all_quotes, ignore_index=True)

        # 上場銘柄一覧を取得
        info_df = fetch_listed_info(config, id_token, logger)

        # スコアリング実行
        result_df = score_stocks(quotes_df, info_df, logger)

        # 検証：空でない、必要なカラムがある
        assert not result_df.empty
        for col in ["Rank", "Code", "CompanyName", "Score"]:
            assert col in result_df.columns

        logger.info("スコアリングテスト成功。出力件数: %d" % len(result_df))

    except Exception as e:
        logger.error(f"スコアリングテスト中に例外発生: {e}")
        raise
