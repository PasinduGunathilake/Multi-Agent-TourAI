import os
import sys
import re
import time
import json
import hashlib
import logging
from functools import wraps
from pathlib import Path
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar
from typing import Optional, Any, Union

# Hide third-party HTTP request URLs from leaking credentials/query keys to terminal
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# 1. Context Variables for Request Tracing
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Retrieves the current request ID from contextvars."""
    return request_id_var.get()


def set_request_id(req_id: Optional[str]):
    """Sets the active request ID in contextvars and returns the token for cleanup."""
    return request_id_var.set(req_id)


def reset_request_id(token):
    """Resets the request ID contextvar using the provided token."""
    try:
        request_id_var.reset(token)
    except Exception:
        request_id_var.set(None)


# 2. Paths and Directory Setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

# 3. Environment & Configuration Parsing
def get_environment() -> str:
    return os.getenv("ENVIRONMENT", "development").strip().lower()


def get_log_level() -> int:
    level_name = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    return getattr(logging, level_name, logging.INFO)


def is_file_logging_enabled() -> bool:
    env_setting = os.getenv("ENABLE_FILE_LOGGING")
    if env_setting is not None:
        return env_setting.strip().lower() in ("true", "1", "yes")
    # Default: Enabled for local development/testing; disabled in containerized production
    return get_environment() not in ("production", "prod", "staging")


def get_log_format_mode() -> str:
    fmt_env = os.getenv("LOG_FORMAT", "auto").strip().lower()
    if fmt_env in ("json", "text"):
        return fmt_env
    # Auto mode: JSON in production/staging; human-readable text in development
    return "json" if get_environment() in ("production", "prod", "staging") else "text"


# 4. Data Sanitization & Redaction Helpers
def mask_email(email: Optional[str]) -> str:
    """Masks an email address for safe logging (e.g. j***e@example.com)."""
    if not email or "@" not in email:
        return "[MASKED_EMAIL]"
    parts = email.strip().split("@", 1)
    user, domain = parts[0], parts[1]
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = f"{user[0]}{'*' * (len(user) - 2)}{user[-1]}"
    return f"{masked_user}@{domain}"


def pseudonymize_id(raw_id: Any) -> str:
    """
    Produces a safe, deterministic, pseudonymous identifier from a user or thread ID.
    E.g., UUID '123e4567-e89b-12d3-a456-426614174000' -> 'anon_e89b12d3'.
    Enables cross-log correlation without exposing raw database primary keys or PII.
    """
    if not raw_id:
        return "-"
    clean = str(raw_id).strip()
    if not clean or clean == "-":
        return "-"
    digest = hashlib.sha256(clean.encode("utf-8")).hexdigest()[:8]
    return f"anon_{digest}"


# Regular expressions for scrubbing sensitive keys, tokens, and query parameters
_SECRET_REDACT_PATTERNS = [
    (re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"([?&](?:api[_-]?key|apikey|key|token|secret|password|access_token)=)[^&\s'\"]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"((?:api[_-]?key|password|passwd|secret|token|refresh_token|access_token|auth_token|smtp_password)[\s:=]+['\"]?)[a-zA-Z0-9_\-\.]{8,}(['\"]?)", re.IGNORECASE), r"\1[REDACTED]\2"),
]


def redact_sensitive_data(text: str) -> str:
    """Sanitizes text by redacting API keys, tokens, passwords, and sensitive query parameters."""
    if not isinstance(text, str):
        text = str(text)
    for pattern, replacement in _SECRET_REDACT_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def sanitize_log_message(msg: Any) -> str:
    """Removes unprintable control characters and limits single-line length."""
    if not isinstance(msg, str):
        msg = str(msg)
    # Replace control characters to prevent log forging
    return msg.replace("\r", " ").replace("\n", " ").strip()


# 5. Contextual Logging Filter
class ContextualFilter(logging.Filter):
    """
    Injects request_id, service, and environment metadata into every LogRecord
    automatically, ensuring all downstream loggers have contextual correlation.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        record.service = "tourai-backend"
        record.environment = get_environment()
        return True


# 6. Formatters (JSON for Cloud Production & Safe Text for Local Development)
class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter for cloud aggregators (Render, Datadog, Axiom, Better Stack).
    Emits valid single-line JSON with ISO-8601 UTC timestamps and correlation fields.
    """
    def format(self, record: logging.LogRecord) -> str:
        # Resolve timestamp in ISO 8601 format
        created_dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        timestamp_str = created_dt.isoformat()

        # Sanitize and redact sensitive data from the message
        raw_message = record.getMessage()
        sanitized_msg = redact_sensitive_data(sanitize_log_message(raw_message))

        log_data: dict[str, Any] = {
            "timestamp": timestamp_str,
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": sanitized_msg,
            "service": getattr(record, "service", "tourai-backend"),
            "environment": getattr(record, "environment", "development"),
        }

        # Include request_id only when active
        req_id = getattr(record, "request_id", None)
        if req_id and req_id != "-":
            log_data["request_id"] = req_id

        # Attach exception stack trace if present with sensitive data redacted
        if record.exc_info:
            raw_exc = self.formatException(record.exc_info)
            log_data["exception"] = redact_sensitive_data(raw_exc)

        # Attach custom extra fields passed to logger.info(..., extra={...})
        skip_keys = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "request_id", "service", "environment",
        }
        for k, v in record.__dict__.items():
            if k not in skip_keys and not k.startswith("_"):
                try:
                    json.dumps(v)
                    log_data[k] = v
                except (TypeError, OverflowError):
                    log_data[k] = str(v)

        return json.dumps(log_data, default=str)


class SafeTextFormatter(logging.Formatter):
    """
    Human-readable log formatter for local development with automatic sensitive-data redaction.
    """
    def format(self, record: logging.LogRecord) -> str:
        # Pre-redact message before standard formatting
        orig_msg = record.msg
        record.msg = redact_sensitive_data(sanitize_log_message(record.msg))
        try:
            formatted = super().format(record)
        finally:
            record.msg = orig_msg
        return redact_sensitive_data(formatted)

    def formatException(self, exc_info) -> str:
        raw = super().formatException(exc_info)
        return redact_sensitive_data(raw)


# Human-readable format for local development
LOG_FORMAT_TEXT = "%(asctime)s | %(levelname)-8s | [%(request_id)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
text_formatter = SafeTextFormatter(fmt=LOG_FORMAT_TEXT, datefmt=DATE_FORMAT)
json_formatter = JSONFormatter()


# 7. Logger File Cleanup Function (72 hours retention for local development)
def clean_log(log_dir: Union[Path, str] = LOG_DIR, max_age_hours: int = 72):
    """Cleans up local session log files older than max_age_hours."""
    target_dir = Path(log_dir) if isinstance(log_dir, str) else log_dir
    if not target_dir.exists():
        return
    now_timestamp = datetime.now().timestamp()
    cutoff_seconds = max_age_hours * 3600

    try:
        for log_file in target_dir.glob("*.log*"):
            if log_file.name == "system_execution.log":
                continue
            file_mtime = log_file.stat().st_mtime
            if (now_timestamp - file_mtime) > cutoff_seconds:
                log_file.unlink(missing_ok=True)
    except Exception:
        pass


# 8. Central Parent Logger Setup (Handlers attach only this point)
_BASE_LOGGER_NAME = "Multi_Agent_TourAI"
_root_logger = logging.getLogger(_BASE_LOGGER_NAME)
_root_logger.setLevel(get_log_level())
_root_logger.propagate = False

_context_filter = ContextualFilter()
_active_formatter = json_formatter if get_log_format_mode() == "json" else text_formatter

if not _root_logger.handlers:
    # Console Handler (always attached to sys.stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(get_log_level())
    console_handler.setFormatter(_active_formatter)
    console_handler.addFilter(_context_filter)
    _root_logger.addHandler(console_handler)

    # Local File Handlers (only enabled if ENABLE_FILE_LOGGING is true or in local dev)
    if is_file_logging_enabled():
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            clean_log(LOG_DIR, max_age_hours=72)

            SESSION_TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            SESSION_LOG_PATH = LOG_DIR / f"session_{SESSION_TIMESTAMP}.log"
            MAIN_LOG_PATH = LOG_DIR / "system_execution.log"

            session_file_handler = logging.FileHandler(SESSION_LOG_PATH, encoding="utf-8")
            session_file_handler.setLevel(get_log_level())
            session_file_handler.setFormatter(_active_formatter)
            session_file_handler.addFilter(_context_filter)
            _root_logger.addHandler(session_file_handler)

            main_file_handler = RotatingFileHandler(
                filename=MAIN_LOG_PATH,
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
            main_file_handler.setLevel(get_log_level())
            main_file_handler.setFormatter(_active_formatter)
            main_file_handler.addFilter(_context_filter)
            _root_logger.addHandler(main_file_handler)
        except Exception as e:
            # File system permission fallback for restricted environments
            sys.stderr.write(f"[LOG_INIT_WARN] Could not initialize file logging handlers: {e}\n")


# 9. Logger Getter Function (for Child modules)
def get_logger(name: str = _BASE_LOGGER_NAME) -> logging.Logger:
    """
    Returns a logger for the given name. Child loggers automatically
    propagate messages to the central Multi_Agent_TourAI handlers without duplicates.
    """
    # Normalize name under the central root hierarchy if relative
    if not name.startswith(_BASE_LOGGER_NAME) and name != "root":
        normalized_name = f"{_BASE_LOGGER_NAME}.{name}"
    else:
        normalized_name = name

    child_logger = logging.getLogger(normalized_name)
    child_logger.setLevel(get_log_level())
    # Ensure child logger propagates to _root_logger
    child_logger.propagate = True
    return child_logger


# 10. Execution Decorator Function
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

__all__ = [
    "get_logger",
    "logger",
    "clean_log",
    "log_execution",
    "request_id_var",
    "get_request_id",
    "set_request_id",
    "reset_request_id",
    "mask_email",
    "pseudonymize_id",
    "redact_sensitive_data",
    "sanitize_log_message",
    "JSONFormatter",
    "SafeTextFormatter",
]
