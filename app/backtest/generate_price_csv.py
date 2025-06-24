'''
app/backtest/generate_price_csv.py
---------------------------------
110 営業日分の OHLCV を J‑Quants API から取得し、
`backtest_data/price_ohlcv.csv` に保存するユーティリティ。

既存 fetcher 群 (`jquants_signin.py`, `trading_days_fetcher.py`,
`daily_quotes_fetcher.py`) と設定ローダを再利用するため、
把握済みのフォルダ構成・関数名は変更しない。

実行例:
    (venv) python -m app.backtest.generate_price_csv
'''

from pathlib import Path
import pandas as pd
from logging import Logger

from app.core.config import load_config
from app.core.logger import setup_logger
from app.data.jquants_signin import get_refresh_token, get_id_token
from app.data.trading_days_fetcher import get_latest_trading_days
from app.data.daily_quotes_fetcher import fetch_daily_quotes

# ------------------------- 定数 ------------------------- #

OUTPUT_CSV = Path("backtest_data/price_ohlcv.csv")
NEEDED_DAYS = 110  # 90 日検証 + 最大 20 日バッファ

# ------------------------- 関数 ------------------------- #

def _fetch_ohlcv(cfg, id_token: str, logger: Logger) -> pd.DataFrame:
    """直近 N 営業日の四本値を取得して連結する。"""
    days = get_latest_trading_days(cfg, id_token, logger, days=NEEDED_DAYS)

    dfs: list[pd.DataFrame] = []
    for day in days:
        df = fetch_daily_quotes(cfg, id_token, logger, target_date=day)
        dfs.append(df[[
            "Date", "Code", "Open", "High", "Low", "Close", "Volume"
        ]])

    merged = pd.concat(dfs, ignore_index=True)
    return merged


def main() -> None:
    """スクリプトのエントリーポイント。"""
    cfg = load_config("configs/config.yaml")
    logger = setup_logger(cfg.logging)

    # 認証
    refresh_token = get_refresh_token(cfg, logger)
    id_token = get_id_token(cfg, refresh_token, logger)

    # データ取得
    price_df = _fetch_ohlcv(cfg, id_token, logger)

    # 保存ディレクトリの作成
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    price_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    logger.info(f"Saved OHLCV: {OUTPUT_CSV}  rows={len(price_df)}")


if __name__ == "__main__":
    main()
