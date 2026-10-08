import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Paths setup 
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# session log paths
SESSION_TIMESTAMP =datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_LOG_PATH = LOG_DIR/f"session_{SESSION_TIMESTAMP}.log"
MAIN_LOG_PATH = LOG_DIR / "system_execution.log"

# formatter
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)


# logger function
def get_logger(name: str = "Multi_Agent_TourAI") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    # console handler - Terminal view
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # session file handler
    session_file_handler = logging.FileHandler(SESSION_LOG_PATH, encoding="utf-8")
    session_file_handler.setLevel(logging.INFO)
    session_file_handler.setFormatter(formatter)
    logger.addHandler(session_file_handler)

    # rotating main file handler
    main_file_handler = RotatingFileHandler(
        filename=MAIN_LOG_PATH,
        maxBytes=5*1024*1024, #5MB
        backupCount=3,
        encoding="utf-8",
    )

    main_file_handler.setLevel(logging.INFO)
    main_file_handler.setFormatter(formatter)
    logger.addHandler(main_file_handler)

    return logger


# logger file clean function
def clean_log(log_dir: Path, max_age_hours: int = 72):
    now_timestamp = datetime.now().timestamp()
    cutoff_seconds = max_age_hours * 3600 #in 3 days after

    try:
        for log_file in log_dir.glob("*.log*"):
            # Exclude the continuous main log file
            if log_file.name == "system_execution.log":
                continue
            file_mtime = log_file.stat().st_mtime
            if (now_timestamp - file_mtime) > cutoff_seconds:
                log_file.unlink(missing_ok=True)
    except Exception:
        pass

# file cleanup
clean_log(LOG_DIR, max_age_hours=72)

# Default logger instance
logger = get_logger("Multi_Agent_TourAI")

__all__ = ["get_logger", "logger", "clean_log"]