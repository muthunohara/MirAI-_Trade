"""app/utils/filters.py

共通フィルタユーティリティ。現在は『東証プライム／スタンダード／グロース』
に絞り込む関数のみを提供する。

他フェーズ（派生指標付与・スコア計算・バックテスト）から再利用することで、
市場コードのハードコーディングを 1 箇所に集約し保守性を高める。
"""

from pandas import DataFrame
from typing import Set

# 東証 3 市場の MarketCode（J-Quants 仕様）
TSE_MARKET_CODES: Set[str] = {"0111", "0112", "0113"}


def keep_tse_sections(df: DataFrame) -> DataFrame:
    """東証プライム・スタンダード・グロース銘柄のみ残す。

    Args:
        df: DataFrame に `MarketCode` 列が含まれていることを想定。

    Returns:
        DataFrame: フィルタ通過銘柄のみを保持したコピー。
    """
    if "MarketCode" not in df.columns:
        raise KeyError("DataFrame に 'MarketCode' 列が存在しません")

    return df[df["MarketCode"].astype(str).isin(TSE_MARKET_CODES)].copy()
