from pathlib import Path
import pytest
from app.core.config import load_config
from app.core.logger import setup_logger
from app.data.trading_days_fetcher import get_latest_trading_days
from app.data.jquants_signin import get_refresh_token, get_id_token

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

def test_get_latest_trading_days(config, id_token, logger):
    try:
        trading_days = get_latest_trading_days(config, id_token, logger, days=6)
        assert isinstance(trading_days, list)
        assert all(isinstance(day, str) for day in trading_days)
        assert len(trading_days) == 6

        log_message = f"取得した営業日: {trading_days}"
        logger.info(log_message)
    except Exception as e:
        logger.error(f"テスト中に例外が発生しました: {e}")
        raise
