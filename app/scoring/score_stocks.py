import pandas as pd
import numpy as np
import re
from logging import Logger

def normalize(code: str) -> str:
    """
    文字列中の数字をすべて抜き出し、先頭4桁を返す。
    例: '218A0' → '2180'

    Args:
        code (str): 証券コード（例: '218A0'）

    Returns:
        str: 正規化された先頭4桁コード（例: '2180'）
    """
    digits = ''.join(re.findall(r'\d', str(code)))
    return digits[:4] if len(digits) >= 4 else ''

def score_stocks(quotes_df: pd.DataFrame, info_df: pd.DataFrame, logger: Logger) -> pd.DataFrame:
    """
    銘柄の株価情報と上場情報を用いてスコアを計算し、ランキングする。

    Args:
        quotes_df (pd.DataFrame): 6営業日分の株価四本値データ。
        info_df (pd.DataFrame): 最新の上場銘柄情報。
        logger (Logger): ロガーインスタンス。

    Returns:
        pd.DataFrame: Rank, Code, CompanyName, Score を含むスコアリング結果（上位40件）。
    """
    # 日付型に変換
    quotes_df["Date"] = pd.to_datetime(quotes_df["Date"]).dt.date

    # 最新営業日を特定
    latest_date = quotes_df["Date"].max()
    latest_df = quotes_df[quotes_df["Date"] == latest_date].copy()

    # NaN除去（Open, Close）
    latest_df = latest_df.dropna(subset=["Open", "Close"])

    # ストップ高・ストップ安除外
    latest_df = latest_df[(latest_df["UpperLimit"] != "1") & (latest_df["LowerLimit"] != "1")]

    # 株価レンジフィルタ（1000〜3000円）
    latest_df = latest_df[(latest_df["Close"] >= 1000) & (latest_df["Close"] <= 3000)]

    # 上場銘柄とマージ
    merged = pd.merge(latest_df, info_df, on="Code", how="inner")

    # 信用銘柄 & 東証上場フィルタ
    merged = merged[merged["MarginCode"].isin(["1", "2"])]
    merged = merged[merged["MarketCode"].isin(["0111", "0112", "0113"])]

    # ETF/ETN/J-REIT 除外のため Code 正規化
    merged["Code4"] = merged["Code"].apply(normalize)

    pat_etf  = r'^(1[3-8]\d{2}|15\d{2}|20\d{2}|2[5-9]\d{2})$'
    pat_reit = r'^(3\d{3}|8\d{3}|92\d{2}|34[5-9]\d)$'

    is_etf_etn = (
        merged["Code4"].str.match(pat_etf, na=False) |
        merged["CompanyName"].str.contains(r'ETF|ETN', case=False, na=False)
    )

    is_reit = (
        merged["Code4"].str.match(pat_reit, na=False) &
        merged["CompanyName"].str.contains('投資法人', na=False)
    )

    merged = merged[~(is_etf_etn | is_reit)].copy()

    logger.info(f"フィルタ通過銘柄数: {len(merged)}")

    # 値幅率 = (High - Low) / Low（最新日）
    merged["RangeRatio"] = (merged["High"] - merged["Low"]) / merged["Low"]

    # TR計算のために quotes_df をソート
    quotes_df = quotes_df.sort_values(["Code", "Date"]).copy()
    quotes_df["PrevClose"] = quotes_df.groupby("Code")["Close"].shift(1)

    # TR = max(High - Low, abs(High - PrevClose), abs(Low - PrevClose))
    quotes_df["TR"] = quotes_df.apply(
        lambda row: max(
            row["High"] - row["Low"],
            abs(row["High"] - row["PrevClose"]),
            abs(row["Low"] - row["PrevClose"])
        ) if pd.notnull(row["PrevClose"]) else np.nan,
        axis=1
    )

    # 5日分のTR平均を銘柄ごとに計算
    atr_df = quotes_df.groupby("Code").tail(5).groupby("Code")["TR"].mean()
    vol_df = quotes_df.groupby("Code").tail(5).groupby("Code")["Volume"].mean()

    # スコア計算用にマッピング
    merged["AtrAvg"] = merged["Code"].map(atr_df)
    merged["VolAvg"] = merged["Code"].map(vol_df)
    merged = merged.dropna(subset=["AtrAvg", "VolAvg", "RangeRatio"])
    merged["Score"] = merged["AtrAvg"] * merged["VolAvg"] * merged["RangeRatio"]

    # ランク付け
    merged["Rank"] = merged["Score"].rank(method="min", ascending=False).astype(int)

    # 上位40件のみ抽出
    top40 = merged.nsmallest(40, "Rank")

    return top40[["Rank", "Code", "CompanyName", "Score"]].sort_values("Rank")
