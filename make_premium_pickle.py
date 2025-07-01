"""
make_premium_pickle.py
----------------------
既存 fetcher と同じ構成:

    cfg  = AppConfig()               # ← 呼び出し側で生成
    id_token = get_id_token(cfg, lg) # ← util (既存)
    dfs = fetch_premium_temp(cfg, id_token, lg, "YYYY-MM-DD")

※ get_id_token は daily_quotes_fetcher と同じヘルパを再利用。
"""

from logging import basicConfig, getLogger
from datetime import date, timedelta          # ← timedelta を追加
import pickle, pathlib, pandas as pd

from app.core.config import load_config                      # ← 変更①
from app.data.jquants_signin import get_refresh_token, get_id_token
from app.data.premium_temp_fetcher import fetch_premium_temp

basicConfig(level="INFO")
log = getLogger("premium_gen")

cfg = load_config("configs/config.yaml")                     # ← 変更②
refresh = get_refresh_token(cfg, log)                        # ← 変更③
id_tok  = get_id_token(cfg, refresh, log)

start = date.today() - timedelta(days=90)     # ← ここを 90 日前に短縮
dfs = []
for d in pd.date_range(start, date.today(), freq="B"):
    res = fetch_premium_temp(cfg, id_tok, log, d.strftime("%Y-%m-%d"))
    for k, df in res.items():
        if df.empty:
            continue
        df = df.assign(Date=d.date(), src=k)
        dfs.append(df)

out = pathlib.Path("backtest_data/premium_data.pkl")
out.parent.mkdir(parents=True, exist_ok=True)
pickle.dump(pd.concat(dfs, ignore_index=True), out.open("wb"))
log.info(f"saved {out} rows={len(dfs)}")
