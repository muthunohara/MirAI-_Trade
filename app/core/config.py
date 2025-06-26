from pathlib import Path
from typing import Literal
from pydantic import BaseModel
import yaml
import os

# Logging設定のPydanticモデル
class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    log_dir: str
    format: str

# J-Quants認証設定のPydanticモデル
class JQuantsAuthConfig(BaseModel):
    email: str
    password: str

# J-Quantsエンドポイント設定のPydanticモデル
class JQuantsEndpointsConfig(BaseModel):
    token_auth_user: str
    token_auth_refresh: str
    trading_calendar: str
    daily_quotes: str
    listed_info: str
    futures_prices: str
    weekly_margin_interest: str
    short_selling_positions: str
    trades_spec: str
    
# J-Quants全体の設定
class JQuantsConfig(BaseModel):
    auth: JQuantsAuthConfig
    endpoints: JQuantsEndpointsConfig

# PostgreSQL接続設定のPydanticモデル
class DatabaseConfig(BaseModel):
    host: str
    port: int
    name: str
    user: str
    password: str

# アプリケーション全体の設定
class AppConfig(BaseModel):
    logging: LoggingConfig
    jquants: JQuantsConfig
    database: DatabaseConfig

def load_config(path: str) -> AppConfig:
    """YAMLファイルと環境変数から設定を読み込む関数"""
    with open(path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    # J-Quants認証情報を環境変数から補完
    raw_config["jquants"]["auth"]["email"] = os.getenv("JQ_EMAIL", "")
    raw_config["jquants"]["auth"]["password"] = os.getenv("JQ_PASSWORD", "")

    # DB接続情報を環境変数から補完
    raw_config["database"]["host"] = os.getenv("DB_HOST", "localhost")
    raw_config["database"]["port"] = int(os.getenv("DB_PORT", 5432))
    raw_config["database"]["name"] = os.getenv("DB_NAME", "mirai_trade_db")
    raw_config["database"]["user"] = os.getenv("DB_USER", "postgres")
    raw_config["database"]["password"] = os.getenv("DB_PASSWORD", "")

    return AppConfig(**raw_config)
