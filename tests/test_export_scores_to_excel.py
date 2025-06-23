import pandas as pd
from pathlib import Path
from app.exporters.export_scores_to_excel import export_scores_to_excel
from app.core.logger import setup_logger
from app.core.config import LoggingConfig
import datetime
import os


def test_export_scores_to_excel():
    # ロガー初期化
    logger = setup_logger(LoggingConfig(
        level="INFO",
        log_dir="./logs",
        format="%(asctime)s %(levelname)s %(message)s"
    ))

    # 仮のスコアDataFrame（score_stocks.py の出力形式と一致）
    data = {
        "Rank": [1, 2],
        "Code": ["1234", "5678"],
        "CompanyName": ["Test Corp A", "Test Corp B"],
        "Score": [123456.78, 98765.43]
    }
    df = pd.DataFrame(data)

    # 出力テスト
    output_dir = "exports"
    export_scores_to_excel(df, output_dir, logger)

    # ファイル存在確認
    date_str = datetime.datetime.today().strftime("%Y%m%d")
    expected_file = Path(output_dir) / f"top40_scores_{date_str}.xlsx"
    assert expected_file.exists(), f"ファイルが存在しません: {expected_file}"

    # 後始末（テストで生成されたファイルを削除）
    # os.remove(expected_file)
    print("✅ test_export_scores_to_excel: PASS")
