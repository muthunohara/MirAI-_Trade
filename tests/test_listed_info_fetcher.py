from pathlib import Path
import pytest
from app.core.config import load_config
from app.core.logger import setup_logger
from app.data.jquants_signin import get_refresh_token, get_id_token
from app.data.listed_info_fetcher import fetch_listed_info

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

# fetch_listed_info のテスト

def test_fetch_listed_info(config, id_token, logger):
    try:
        df = fetch_listed_info(config, id_token, logger)

        # DataFrame が空でないことを検証
        assert df is not None
        assert not df.empty

        # 特定のカラムが存在することを検証
        required_columns = ["Code", "CompanyName", "MarketCode", "MarginCode"]
        for col in required_columns:
            assert col in df.columns

        logger.info(f"取得した上場銘柄一覧データの件数: {len(df)}")
    except Exception as e:
        logger.error(f"上場銘柄一覧データ取得中に例外が発生しました: {e}")
        raise
