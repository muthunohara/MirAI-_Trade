"""app/scoring/score_up.py

Score_up スコアリングロジック（新順張り指標）。

- 事前に `add_derived_cols.py` で付与された派生カラムを利用。
- 上場区分フィルタは `app.utils.filters.keep_tse_sections()` を使用。
- ETF/ETN・J-REIT/インフラファンド除外は `Code4`+`CompanyName` 方式。
- パラメータ (a,b,c,d, TopN) は関数引数で上書き可能。

戻り値は Rank, Code, CompanyName, Score_up を含む DataFrame。
"""

from __future__ import annotations

import re
from typing import Tuple
import pandas as pd
import numpy as np
from logging import Logger

from app.utils.filters import keep_tse_sections

# ----------------------------------------------------------------------
# ヘルパ
# ----------------------------------------------------------------------

def _normalize(code: str) -> str:
    """数字のみ抽出→先頭4桁。"""
    digits = "".join(re.findall(r"\d", str(code)))
    return digits[:4] if len(digits) >= 4 else ""

# ETF / ETN, REIT 判定パターン
PAT_ETF = re.compile(r"^(1[3-8]\d{2}|15\d{2}|20\d{2}|2[5-9]\d{2})$")
PAT_REIT = re.compile(r"^(3\d{3}|8\d{3}|92\d{2}|34[5-9]\d)$")

# ----------------------------------------------------------------------
# メイン API
# ----------------------------------------------------------------------

def score_up(
    df: pd.DataFrame,
    info_df: pd.DataFrame,
    logger: Logger,
    params: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    top_n: int = 40,
) -> pd.DataFrame:
    """Score_up を計算し TopN 銘柄を返す。

    Args:
        df: OHLCV + 派生指標 DataFrame（add_derived_cols.py 出力）
        info_df: 上場銘柄一覧 DataFrame
        logger: ロガー
        params: (a,b,c,d) 係数タプル
        top_n: 抽出銘柄数

    Returns:
        DataFrame: Rank, Code, CompanyName, Score_up
    """

    a, b, c, d = params

    # ---------------- 上場区分フィルタ ---------------- #
    info_df = keep_tse_sections(info_df)

    # 最新営業日を取得
    latest_day = df["Date"].max()
    latest = df[df["Date"] == latest_day].copy()

    # マージ
    merged = pd.merge(latest, info_df, on="Code", how="inner")

    # ETF / ETN / REIT 除外
    merged["Code4"] = merged["Code"].apply(_normalize)

    is_etf = merged["Code4"].str.match(PAT_ETF, na=False) | merged["CompanyName"].str.contains(r"ETF|ETN", case=False, na=False)
    is_reit = merged["Code4"].str.match(PAT_REIT, na=False) & merged["CompanyName"].str.contains("投資法人", na=False)

    merged = merged[~(is_etf | is_reit)].copy()

    # NaN を落とす
    needed_cols = ["Vol_5", "Vol_20", "ATR_5", "ATR_20", "Momentum_2", "PullUp"]
    merged[needed_cols] = merged[needed_cols].fillna(0)

    # Momentum_2 が負なら 0
    merged["Momentum_2_pos"] = merged["Momentum_2"].clip(lower=0)

    # --- 10 % 急騰・急落を除外 ---
    merged["OneDayRet"] = merged.groupby("Code")["Close"].pct_change()
    spike_mask = merged["OneDayRet"].abs() >= 0.10   # ±10 % 以上
    merged.loc[spike_mask, needed_cols] = 0
    # ------------------------------
    
    # スコア計算
    merged["Score_up"] = (
        (merged["Vol_5"] / merged["Vol_20"]) ** a *
        (merged["ATR_5"] / merged["ATR_20"]) ** b *
        (merged["Momentum_2_pos"]) ** c *
        (merged["PullUp"]) ** d
    )

    merged = merged.replace([np.inf, -np.inf], np.nan).dropna(subset=["Score_up"])

    # ランク付け
    merged["Rank"] = merged["Score_up"].rank(method="min", ascending=False).astype(int)
    top = merged.nsmallest(top_n, "Rank")

    logger.debug(
    "Score_up 完了: %d → 上位%d件", len(merged), len(top)
    )
    
    return top[["Rank", "Code", "CompanyName", "Score_up"]].sort_values("Rank").reset_index(drop=True)
