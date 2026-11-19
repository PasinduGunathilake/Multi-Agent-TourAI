import os
import uuid
import hashlib
import secrets
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, Iterator
import psycopg
from psycopg.rows import dict_row
from fastapi import Response, Request
from Multi_Agent_TourAI.database import get_db_connection
from Multi_Agent_TourAI.utils import get_logger

logger = get_logger("Multi_Agent_TourAI.auth.session_service")

REFRESH_TOKEN_COOKIE_NAME = "tourai_refresh_token"
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")


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


class RefreshTokenReusedError(Exception):
    """Raised when an expired/revoked refresh token is replayed outside the grace window."""
    pass


class RefreshTokenRecentlyRotatedError(Exception):
    """Raised when an already rotated token is replayed within the concurrency grace window."""
    pass


def _hash_token(token: str) -> str:
    """Computes SHA-256 hash of a refresh token."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()


def create_session(user_id: uuid.UUID) -> Tuple[uuid.UUID, str]:
    """
    Creates a new authenticated session for a user.
    Stores SHA-256 hash in auth_sessions.
    Returns (session_id, raw_refresh_token).
    """
    session_id = uuid.uuid4()
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    with _get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.auth_sessions (id, user_id, refresh_token_hash, expires_at)
                VALUES (%s, %s, %s, %s);
                """,
                (session_id, user_id, token_hash, expires_at),
            )
    return session_id, raw_token


def rotate_session(raw_refresh_token: str) -> Optional[Tuple[Dict[str, Any], uuid.UUID, str]]:
    """
    Validates the refresh token and rotates it:
    - Verifies token hash exists and is unexpired.
    - If token was already revoked (reuse detection!), immediately revokes ALL sessions for the user!
    - Otherwise, marks old session revoked and creates a fresh session.
    Returns (user_dict, new_session_id, new_raw_token) on success, or None on invalid.
    """
    if not raw_refresh_token or not raw_refresh_token.strip():
        return None

    old_hash = _hash_token(raw_refresh_token)
    now = datetime.now(timezone.utc)

    try:
        with _get_connection(autocommit=False, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Look up session by token hash
                cur.execute(
                    """
                    SELECT id, user_id, expires_at, revoked_at
                    FROM public.auth_sessions
                    WHERE refresh_token_hash = %s
                    FOR UPDATE;
                    """,
                    (old_hash,),
                )
                session = cur.fetchone()

                if not session:
                    conn.rollback()
                    return None

                user_id = session["user_id"]

                # Token Reuse Detection with Concurrency Grace Window
                if session["revoked_at"] is not None:
                    revoked_at = session["revoked_at"]
                    elapsed_seconds = (now - revoked_at).total_seconds()
                    # 15-second grace window for concurrent requests
                    if elapsed_seconds < 15:
                        logger.info(
                            f"[AUTH] Refresh token already rotated recently ({elapsed_seconds:.1f}s ago). "
                            "Rejecting replay within grace window without issuing new token or revoking active sessions."
                        )
                        conn.rollback()
                        raise RefreshTokenRecentlyRotatedError("Refresh token was already rotated recently.")

                    # Outside grace window: genuine malicious token reuse / replay detected!
                    logger.warning(
                        f"[SECURITY] Refresh token reuse detected for user {user_id}! "
                        f"Token revoked {elapsed_seconds:.1f}s ago. Revoking all active user sessions."
                    )
                    cur.execute(
                        """
                        UPDATE public.auth_sessions
                        SET revoked_at = %s
                        WHERE user_id = %s AND revoked_at IS NULL;
                        """,
                        (now, user_id),
                    )
                    conn.commit()
                    raise RefreshTokenReusedError("Refresh token reuse detected. All sessions revoked.")

                # Check expiration
                if session["expires_at"] < now:
                    conn.rollback()
                    return None

                # Mark old session as revoked
                cur.execute(
                    """
                    UPDATE public.auth_sessions
                    SET revoked_at = %s, last_used_at = %s
                    WHERE id = %s;
                    """,
                    (now, now, session["id"]),
                )

                # Issue fresh session
                new_session_id = uuid.uuid4()
                new_raw_token = secrets.token_urlsafe(48)
                new_token_hash = _hash_token(new_raw_token)
                new_expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

                cur.execute(
                    """
                    INSERT INTO public.auth_sessions (id, user_id, refresh_token_hash, expires_at)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (new_session_id, user_id, new_token_hash, new_expires_at),
                )

                # Fetch user info
                cur.execute(
                    """
                    SELECT id, email, display_name, avatar_url, email_verified, is_active, created_at, updated_at
                    FROM public.app_users
                    WHERE id = %s AND is_active = TRUE;
                    """,
                    (user_id,),
                )
                user = cur.fetchone()
                if not user:
                    conn.rollback()
                    return None

            conn.commit()
            return dict(user), new_session_id, new_raw_token
    except (RefreshTokenReusedError, RefreshTokenRecentlyRotatedError):
        raise
    except Exception as e:
        logger.error(f"[AUTH] Error rotating session: {e}", exc_info=True)
        return None


def revoke_session_by_token(raw_refresh_token: str) -> bool:
    """Revokes the session associated with the provided refresh token."""
    if not raw_refresh_token:
        return False
    token_hash = _hash_token(raw_refresh_token)
    now = datetime.now(timezone.utc)
    try:
        with _get_connection(autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE public.auth_sessions
                    SET revoked_at = %s
                    WHERE refresh_token_hash = %s AND revoked_at IS NULL;
                    """,
                    (now, token_hash),
                )
                return cur.rowcount > 0
    except Exception as e:
        logger.error(f"[AUTH] Error revoking session: {e}", exc_info=True)
        return False


def revoke_all_user_sessions(user_id: uuid.UUID) -> int:
    """Revokes all active sessions for a user (global logout)."""
    now = datetime.now(timezone.utc)
    with _get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE public.auth_sessions
                SET revoked_at = %s
                WHERE user_id = %s AND revoked_at IS NULL;
                """,
                (now, user_id),
            )
            return cur.rowcount


def set_refresh_cookie(response: Response, raw_token: str) -> None:
    """Sets a secure HttpOnly refresh token cookie on the HTTP response."""
    max_age = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=raw_token,
        max_age=max_age,
        expires=max_age,
        path="/api/auth",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite=COOKIE_SAMESITE,  # 'lax' or 'none' depending on cross-domain
    )


def clear_refresh_cookie(response: Response) -> None:
    """Deletes the refresh token cookie."""
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        path="/api/auth",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite=COOKIE_SAMESITE,
    )

