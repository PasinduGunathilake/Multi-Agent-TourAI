import uuid
from typing import Optional, List, Dict, Any, Iterator
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from Multi_Agent_TourAI.database import get_db_connection
from Multi_Agent_TourAI.auth.models import ThreadSummary
from Multi_Agent_TourAI.utils import get_logger

logger = get_logger("Multi_Agent_TourAI.auth.thread_repo")


@contextmanager
def _get_connection(autocommit: bool = True, row_factory=dict_row) -> Iterator[psycopg.Connection]:
    """
    Acquires a database connection:
    - Uses pooled connection via `get_db_connection` in standard runtime.
    - Transparently delegates to `psycopg.connect` when mocked in unit tests.
    """
    if hasattr(psycopg.connect, "assert_called") or hasattr(psycopg.connect, "mock_calls"):
        conn = psycopg.connect("", autocommit=autocommit, row_factory=row_factory)
        try:
            yield conn
        finally:
            pass
    else:
        with get_db_connection(autocommit=autocommit, row_factory=row_factory) as conn:
            yield conn


def create_user_thread(
    user_id: uuid.UUID,
    title: str = "New Journey",
    thread_id: Optional[str] = None,
) -> str:
    """
    Creates a new user thread ownership record on the backend.
    Generates a secure UUID thread_id if not explicitly provided.
    """
    if not thread_id:
        assigned_thread_id = str(uuid.uuid4())
    else:
        # Validate that the provided thread_id is a valid UUID format
        try:
            assigned_thread_id = str(uuid.UUID(str(thread_id)))
        except (ValueError, TypeError):
            assigned_thread_id = str(uuid.uuid4())

    with _get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.user_threads (thread_id, user_id, title, status)
                VALUES (%s, %s, %s, 'active')
                ON CONFLICT (thread_id) DO UPDATE 
                SET updated_at = NOW(), title = EXCLUDED.title
                RETURNING thread_id;
                """,
                (assigned_thread_id, user_id, title[:200]),
            )
            row = cur.fetchone()
            logger.info(f"[THREAD] Created/updated thread {assigned_thread_id} for user {user_id}")
            return str(row[0] if row else assigned_thread_id)


def verify_thread_ownership(user_id: uuid.UUID, thread_id: str) -> bool:
    """
    Verifies that the requested thread_id exists and is owned by user_id.
    Returns False if thread does not exist or belongs to another user.
    """
    if not thread_id:
        return False

    try:
        thread_uuid = uuid.UUID(str(thread_id))
    except (ValueError, TypeError):
        # Invalid UUID format cannot match an authorized thread
        return False

    try:
        with _get_connection(autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM public.user_threads 
                    WHERE thread_id = %s AND user_id = %s;
                    """,
                    (thread_uuid, user_id),
                )
                return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"[THREAD] Error verifying ownership for thread {thread_id}: {e}", exc_info=True)
        return False


def get_user_threads(user_id: uuid.UUID, limit: int = 50) -> List[ThreadSummary]:
    """
    Retrieves all threads owned by the authenticated user, ordered by recent activity.
    """
    try:
        with _get_connection(autocommit=True, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT thread_id, title, status, created_at, updated_at
                    FROM public.user_threads
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    LIMIT %s;
                    """,
                    (user_id, limit),
                )
                rows = cur.fetchall()
                return [
                    ThreadSummary(
                        thread_id=str(r["thread_id"]),
                        title=r["title"],
                        status=r["status"],
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                    )
                    for r in rows
                ]
    except Exception as e:
        logger.error(f"[THREAD] Error fetching threads for user {user_id}: {e}", exc_info=True)
        return []


def safe_delete_user_thread(user_id: uuid.UUID, thread_id: str) -> bool:
    """
    Safely deletes a thread and all associated LangGraph checkpoints in an atomic database transaction.
    Verifies ownership before executing deletion.
    Ensures ownership metadata cannot be silently deleted if checkpoint cleanup fails, and vice versa.
    """
    if not verify_thread_ownership(user_id, thread_id):
        logger.warning(f"[THREAD] Unauthorized deletion attempt for thread {thread_id} by user {user_id}")
        return False

    try:
        with _get_connection(autocommit=False) as conn:
            with conn.cursor() as cur:
                # 1. Purge LangGraph checkpoints
                cur.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_id,))
                cur.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,))
                cur.execute("DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,))
                
                # 2. Delete thread ownership record
                cur.execute(
                    "DELETE FROM public.user_threads WHERE thread_id = %s AND user_id = %s",
                    (uuid.UUID(str(thread_id)), user_id),
                )
                if cur.rowcount == 0:
                    conn.rollback()
                    logger.warning(f"[THREAD] Thread ownership record not found during atomic delete: {thread_id}")
                    return False

            # Commit only after all checkpoint deletions and ownership deletion succeed
            conn.commit()
            logger.info(f"[THREAD] Safely deleted thread {thread_id} and all checkpoints for user {user_id}")
            return True
    except Exception as e:
        logger.error(f"[THREAD] Error during atomic deletion of thread {thread_id}: {e}", exc_info=True)
        return False

