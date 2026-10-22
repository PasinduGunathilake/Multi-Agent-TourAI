import sys
import time
from functools import wraps
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Hide httpx request URLs from printing API keys to terminal
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# 1. Paths setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 2. Session log paths
SESSION_TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_LOG_PATH = LOG_DIR / f"session_{SESSION_TIMESTAMP}.log"
MAIN_LOG_PATH = LOG_DIR / "system_execution.log"

# 3. Formatter
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)


# 4. Logger file clean function (72 hours retention)
def clean_log(log_dir: Path = LOG_DIR, max_age_hours: int = 72):
    now_timestamp = datetime.now().timestamp()
    cutoff_seconds = max_age_hours * 3600

    try:
        for log_file in log_dir.glob("*.log*"):
            if log_file.name == "system_execution.log":
                continue
            file_mtime = log_file.stat().st_mtime
            if (now_timestamp - file_mtime) > cutoff_seconds:
                log_file.unlink(missing_ok=True)
    except Exception:
        pass


# Run cleanup once on initialization (3 day history clean)
clean_log(LOG_DIR, max_age_hours=72)


# 5. Central Parent Logger Setup (Handlers attach only this point)
_BASE_LOGGER_NAME = "Multi_Agent_TourAI"
_root_logger = logging.getLogger(_BASE_LOGGER_NAME)
_root_logger.setLevel(logging.INFO)

if not _root_logger.handlers:
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    _root_logger.addHandler(console_handler)

    # Session File Handler (Current run log)
    session_file_handler = logging.FileHandler(SESSION_LOG_PATH, encoding="utf-8")
    session_file_handler.setLevel(logging.INFO)
    session_file_handler.setFormatter(formatter)
    _root_logger.addHandler(session_file_handler)

    # Rotating Main File Handler (Max 5MB)
    main_file_handler = RotatingFileHandler(
        filename=MAIN_LOG_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    main_file_handler.setLevel(logging.INFO)
    main_file_handler.setFormatter(formatter)
    _root_logger.addHandler(main_file_handler)


# 6. Logger Getter Function (for Child modules)
def get_logger(name: str = _BASE_LOGGER_NAME) -> logging.Logger:
    """
    Returns a logger for the given name. Child loggers automatically
    propagate messages to the central Multi_Agent_TourAI handlers without duplicates.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


# 7. Decorator Function
def log_execution(func):
    """
    A decorator that automatically logs a function's start, completion, 
    execution latency, and full stack trace if an exception occurs.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_logger = get_logger(func.__module__)
        func_logger.info(f"Started: {func.__name__}")
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = round(time.time() - start_time, 2)
            func_logger.info(f"Finished: {func.__name__} (took {duration}s)")
            return result
        except Exception as e:
            # GraphInterrupt is LangGraph's internal pause mechanism, not an error
            if e.__class__.__name__ == "GraphInterrupt":
                raise e
            duration = round(time.time() - start_time, 2)
            func_logger.error(
                f"Failed: {func.__name__} after {duration}s | Error: {str(e)}", 
                exc_info=True
            )
            raise e

    return wrapper


# Default instance
logger = _root_logger

__all__ = ["get_logger", "logger", "clean_log", "log_execution"]
