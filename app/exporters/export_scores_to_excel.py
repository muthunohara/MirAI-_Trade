import pandas as pd
from pathlib import Path
from datetime import datetime
from logging import Logger


def export_scores_to_excel(df: pd.DataFrame, output_dir: str, logger: Logger) -> None:
    """
    スコアリング結果DataFrameをExcelファイルとして出力する。

    Args:
        df (pd.DataFrame): スコアリング済み上位40銘柄のDataFrame。
        output_dir (str): Excelファイルの出力ディレクトリパス。
        logger (Logger): ロガーインスタンス。

    Returns:
        None
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    date_str = datetime.today().strftime("%Y%m%d")
    file_name = f"top40_scores_{date_str}.xlsx"
    file_path = Path(output_dir) / file_name

    logger.info(f"Excel出力開始: {file_path}")
    df.to_excel(file_path, index=False)
    logger.info("Excel出力完了")
