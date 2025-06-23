import psycopg2
from logging import Logger
from app.core.config import AppConfig


class DBClient:
    """
    PostgreSQL への接続と切断を管理するクラス。
    インスタンス生成時に接続し、破棄時に自動切断する。
    """

    def __init__(self, config: AppConfig, logger: Logger):
        self.logger = logger
        try:
            self.conn = psycopg2.connect(
                host=config.database.host,
                port=config.database.port,
                dbname=config.database.name,
                user=config.database.user,
                password=config.database.password
            )
            self.logger.info("PostgreSQL に接続しました。")
        except Exception as e:
            self.logger.error(f"DB接続エラー: {e}")
            raise

    def __del__(self):
        try:
            if hasattr(self, "conn"):
                self.conn.close()
            self.logger.info("PostgreSQL 接続を切断しました。")
        except Exception as e:
            self.logger.warning(f"DB切断時のエラー: {e}")
