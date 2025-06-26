"""
app/backtest/add_derived_cols.py
--------------------------------
110 営業日分 OHLCV CSV (`backtest_data/price_ohlcv.csv`) に
派生指標を追加し、`backtest_data/price_ohlcv_derived.csv` として保存する。

※ OHLCV には MarketCode が無いので市場フィルタは行わない。
   ETF / REIT 判定はスコアリング層 (score_up.py) で実施する。
"""

from pathlib import Path
import pandas as pd
from logging import getLogger, basicConfig, INFO

INPUT_CSV = Path("backtest_data/price_ohlcv.csv")
OUTPUT_CSV = Path("backtest_data/price_ohlcv_derived.csv")

basicConfig(level=INFO, format="%(levelname)s  %(message)s")
logger = getLogger("add_derived_cols")


# ----------------------------------------------------------------------
# 派生指標付与
# ----------------------------------------------------------------------
def add_derived_cols(df: pd.DataFrame) -> pd.DataFrame:
    """派生指標を DataFrame に付与する。

    Args:
        df: OHLCV DataFrame (Date, Code, Open, High, Low, Close, Volume)

    Returns:
        DataFrame: 派生指標列を追加した新 DataFrame
    """
    df = df.sort_values(["Code", "Date"]).copy()
    grp = df.groupby("Code", group_keys=False)

    # 出来高平均
    df["Vol_5"] = (
        grp["Volume"].rolling(5, min_periods=5).mean().reset_index(level=0, drop=True)
    )
    df["Vol_20"] = (
        grp["Volume"].rolling(20, min_periods=10).mean().reset_index(level=0, drop=True)
    )

    # ATR 系
    df["ATR_1"] = df["High"] - df["Low"]
    df["ATR_5"] = (
        grp["ATR_1"].rolling(5, min_periods=5).mean().reset_index(level=0, drop=True)
    )
    df["ATR_20"] = (
        grp["ATR_1"].rolling(20, min_periods=10).mean().reset_index(level=0, drop=True)
    )

    # Momentum_2
    df["Close_shift1"] = grp["Close"].shift(1)
    df["Close_shift2"] = grp["Close"].shift(2)
    df["Momentum_2"] = (df["Close_shift1"] / df["Close_shift2"] - 1).round(6)

    # PullUp
    df["High_shift1"] = grp["High"].shift(1)
    df["Low_shift1"] = grp["Low"].shift(1)
    df["PullUp"] = (
        (df["Close_shift1"] - df["Low_shift1"])
        / (df["High_shift1"] - df["Low_shift1"])
        + 0.5
    ).round(6)

    # 不要列削除
    df.drop(
        columns=[
            "Close_shift1",
            "Close_shift2",
            "High_shift1",
            "Low_shift1",
        ],
        inplace=True,
    )

    return df


# ----------------------------------------------------------------------
# CLI entry
# ----------------------------------------------------------------------
def main() -> None:
    if not INPUT_CSV.exists():
        logger.error("Input file not found: %s", INPUT_CSV)
        return

    logger.info("Loading %s", INPUT_CSV)
    raw = pd.read_csv(INPUT_CSV, parse_dates=["Date"])

    derived = add_derived_cols(raw)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    derived.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    logger.info("Saved %s  rows=%d", OUTPUT_CSV, len(derived))


if __name__ == "__main__":
    main()
