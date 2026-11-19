import os
import threading
from contextlib import contextmanager
from typing import Optional, Iterator, Dict, Any
from urllib.parse import urlparse
import certifi
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from Multi_Agent_TourAI.utils import get_logger

# Windows SSL certificate path fix
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()
logger = get_logger("Multi_Agent_TourAI.database.connection")

# Pool Configuration Defaults
DEFAULT_POOL_MIN = int(os.getenv("DB_POOL_MIN_SIZE", "0"))
DEFAULT_POOL_MAX = int(os.getenv("DB_POOL_MAX_SIZE", "10"))
DEFAULT_POOL_TIMEOUT = float(os.getenv("DB_POOL_TIMEOUT", "10.0"))
DEFAULT_POOL_MAX_IDLE = float(os.getenv("DB_POOL_MAX_IDLE", "300.0"))

_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def get_database_url() -> str:
    """
    Retrieves and normalizes the PostgreSQL database URL with sslmode=require.
    Checks DATABASE_URL first, then POSTGRESQL_URL.
    """
    db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRESQL_URL")
    if not db_url or not db_url.strip():
        raise ValueError(
            "DATABASE_URL is missing. Please configure DATABASE_URL in your environment."
        )

    db_url = db_url.strip()
    if "sslmode" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}sslmode=require"

    return db_url


def create_connection_pool(
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    timeout: Optional[float] = None,
    max_idle: Optional[float] = None,
    open_pool: bool = True,
) -> ConnectionPool:
    """
    Factory function creating a configured psycopg_pool.ConnectionPool.
    Sets row_factory=dict_row by default for consistent dictionary rows.
    """
    db_url = get_database_url()
    parsed = urlparse(db_url)
    resolved_min = DEFAULT_POOL_MIN if min_size is None else min_size
    resolved_max = DEFAULT_POOL_MAX if max_size is None else max_size
    resolved_timeout = DEFAULT_POOL_TIMEOUT if timeout is None else timeout
    resolved_idle = DEFAULT_POOL_MAX_IDLE if max_idle is None else max_idle

    logger.info(
        f"Initializing PostgreSQL Connection Pool [Host: '{parsed.hostname}', "
        f"DB: '{parsed.path[1:]}', Min: {resolved_min}, "
        f"Max: {resolved_max}]"
    )

    pool = ConnectionPool(
        conninfo=db_url,
        min_size=resolved_min,
        max_size=resolved_max,
        timeout=resolved_timeout,
        max_idle=resolved_idle,
        open=open_pool,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
        },
    )
    return pool


def get_connection_pool() -> ConnectionPool:
    """
    Thread-safe singleton accessor for the application-wide connection pool.
    Initializes lazily on first call if not already opened by application lifespan.
    """
    global _pool
    if _pool is not None and not _pool.closed:
        return _pool

    with _pool_lock:
        if _pool is not None and not _pool.closed:
            return _pool
        _pool = create_connection_pool(open_pool=True)
        return _pool


def close_connection_pool():
    """
    Closes the connection pool and drains all connections gracefully.
    Used during FastAPI shutdown and test teardown.
    """
    global _pool
    with _pool_lock:
        if _pool is not None and not _pool.closed:
            logger.info("Closing PostgreSQL connection pool and draining connections...")
            try:
                _pool.close()
            except Exception as e:
                logger.warning(f"Error while closing database pool: {e}")
        _pool = None


def reset_pool_cache():
    """Resets the singleton pool reference (primarily for testing and mock injection)."""
    global _pool
    with _pool_lock:
        if _pool is not None and not _pool.closed:
            try:
                _pool.close()
            except Exception:
                pass
        _pool = None


@contextmanager
def get_db_connection(
    autocommit: bool = True,
    row_factory=dict_row,
    timeout: Optional[float] = None,
) -> Iterator[psycopg.Connection]:
    """
    Context manager that checks out a connection from the pool and returns it on exit.
    
    Guarantees:
      - Automatically rolls back uncommitted changes on exception.
      - Automatically returns connection to the pool upon exiting context.
      - Sets requested autocommit and row_factory on checkout and resets them on release.
    """
    pool = get_connection_pool()
    checkout_timeout = timeout or DEFAULT_POOL_TIMEOUT

    with pool.connection(timeout=checkout_timeout) as conn:
        orig_autocommit = conn.autocommit
        orig_row_factory = conn.row_factory
        try:
            if conn.autocommit != autocommit:
                conn.autocommit = autocommit
            if conn.row_factory != row_factory:
                conn.row_factory = row_factory

            yield conn

            if not autocommit:
                conn.commit()
        except Exception:
            if not autocommit and not conn.closed:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise
        finally:
            if not conn.closed:
                try:
                    conn.autocommit = orig_autocommit
                    conn.row_factory = orig_row_factory
                except Exception:
                    pass


def check_database_health() -> Dict[str, Any]:
    """Performs a quick SELECT 1 query to confirm database pool health and connectivity."""
    pool = None
    try:
        pool = get_connection_pool()
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "pool_closed": True}

    stats = {
        "pool_min": pool.min_size if pool else None,
        "pool_max": pool.max_size if pool else None,
        "pool_closed": pool.closed if pool else True,
    }
    try:
        with get_db_connection(autocommit=True, timeout=2.0) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                row = cur.fetchone()
                if row is not None:
                    return {"status": "healthy", **stats}
        return {"status": "unhealthy", "error": "Query returned no rows", **stats}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), **stats}


__all__ = [
    "get_database_url",
    "create_connection_pool",
    "get_connection_pool",
    "close_connection_pool",
    "reset_pool_cache",
    "get_db_connection",
    "check_database_health",
]
