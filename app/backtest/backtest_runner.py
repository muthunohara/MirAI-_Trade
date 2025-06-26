"""app/backtest/backtest_runner.py

Score_up バックテスト実行スクリプト（90 営業日）。
1. 派生指標付き CSV を読み込み
2. 上場区分フィルタ & ETF/REIT フィルタは score_up 内部に委譲
3. 90 営業日ループでバスケットリターン計算
4. 結果 CSV / 資産曲線 PNG を保存
5. 指標を metrics.py で算出
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple
import matplotlib.pyplot as plt
import pandas as pd
from logging import getLogger, basicConfig, WARNING

from app.scoring.score_up import score_up
from app.backtest.metrics import calc_metrics
from app.core.config import load_config
from app.data.listed_info_fetcher import fetch_listed_info
from app.data.jquants_signin import get_refresh_token, get_id_token

INPUT_CSV = Path("backtest_data/price_ohlcv_derived.csv")
OUT_CSV = Path("backtest_results/results_90d.csv")
OUT_PNG = Path("backtest_results/equity_curve.png")

basicConfig(level=WARNING, format="%(levelname)s  %(message)s")
logger = getLogger("backtest_runner")


# ----------------------------------------------------------------------
# Backtest
# ----------------------------------------------------------------------

def run_backtest(
    price_df: pd.DataFrame,
    info_df: pd.DataFrame,
    coeffs: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    top_n: int = 40,
) -> pd.DataFrame:
    """90 営業日のバックテストを実行し、日次リターン DataFrame を返す。"""

    price_df = price_df.sort_values(["Date", "Code"]).copy()
    unique_days = sorted(price_df["Date"].unique())
    trade_days = unique_days[-90:]

    # ── 出来高 & ボラティリティ フィルタ ──────────────────────
    price_df = price_df[
        (price_df["Vol_20"] > 5e5) &                         # 20日平均出来高 50万株超
        (price_df["ATR_20"] / price_df["Close"] < 0.08)      # 変動率 8％ 未満
    ]
    # --------------------------------------------------------------

    results = []
    for trade_day in trade_days:
        prev_day = max(d for d in unique_days if d < trade_day)

        # 前日までのデータで Score_up
        universe = price_df[price_df["Date"] <= prev_day]
        score_df = score_up(universe, info_df, logger, coeffs, top_n)
        picks = score_df["Code"].tolist()

        # 当日の Open / Close
        day_df = price_df[price_df["Date"] == trade_day]
        open_px = day_df.set_index("Code")["Open"].reindex(picks)
        close_px = day_df.set_index("Code")["Close"].reindex(picks)
        ret = ((close_px - open_px) / open_px).mean() - 0.0005   # 0.05 %

        results.append({"Date": trade_day, "Ret": round(ret, 4)})

    return pd.DataFrame(results)


# ----------------------------------------------------------------------
# CLI entry
# ----------------------------------------------------------------------

def main() -> None:
    if not INPUT_CSV.exists():
        logger.error("Input CSV not found: %s", INPUT_CSV)
        return

    price_df = pd.read_csv(INPUT_CSV, parse_dates=["Date"])

    cfg = load_config("configs/config.yaml")
    refresh = get_refresh_token(cfg, logger)
    id_tok = get_id_token(cfg, refresh, logger)
    info_df = fetch_listed_info(cfg, id_tok, logger)

    res_df = run_backtest(price_df, info_df)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    logger.info("Saved %s", OUT_CSV)

    # 指標計算
    metrics = calc_metrics(res_df["Ret"])
    logger.info("Metrics: %s", metrics)

    # 資産曲線
    equity = (1 + res_df["Ret"]).cumprod()
    plt.figure()
    plt.plot(res_df["Date"], equity)
    plt.title("Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(True)
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=120, bbox_inches="tight")
    plt.close()
    logger.info("Saved %s", OUT_PNG)


if __name__ == "__main__":
    main()
