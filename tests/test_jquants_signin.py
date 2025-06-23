from pathlib import Path
import logging
import pytest
from app.core.config import load_config
from app.core.logger import setup_logger
from app.data.jquants_signin import get_refresh_token, get_id_token

# コンフィグファイルの絶対パスを構築（テストからの相対パス）
CONFIG_PATH = Path(__file__).parent.parent / "configs" / "config.yaml"

@pytest.fixture(scope="module")
def config():
    return load_config(str(CONFIG_PATH))

@pytest.fixture(scope="module")
def logger(config):
    return setup_logger(config.logging)

def test_get_refresh_token(config, logger):
    refresh_token = get_refresh_token(config, logger)
    assert isinstance(refresh_token, str)
    assert len(refresh_token) > 0

def test_get_id_token(config, logger):
    refresh_token = get_refresh_token(config, logger)
    id_token = get_id_token(config, refresh_token, logger)
    assert isinstance(id_token, str)
    assert len(id_token) > 0
