import logging
from datetime import datetime
from pathlib import Path
from app.core.config import LoggingConfig

def setup_logger(config: LoggingConfig) -> logging.Logger:
    logger = logging.getLogger("MirAI_Trade")
    logger.setLevel(getattr(logging, config.level.upper()))

    formatter = logging.Formatter(config.format)

    # ログファイル名に日付を含める
    date_str = datetime.today().strftime("%Y-%m-%d")
    log_file_name = f"MirAI_Trade_{date_str}.log"
    log_file_path = Path(config.log_dir) / log_file_name
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    fh = logging.FileHandler(log_file_path, encoding="utf-8")
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(sh)

    return logger
