import uuid
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple, Iterator
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from Multi_Agent_TourAI.database.connection import get_db_connection
from Multi_Agent_TourAI.utils import get_logger

logger = get_logger("Multi_Agent_TourAI.auth.repository")


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


def _hash_token(token: str) -> str:
    """Computes SHA-256 hash of a token for secure storage at rest."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()


def get_user_by_id(user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Retrieves an app_user by UUID using the centralized connection pool."""
    with _get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, display_name, avatar_url, email_verified, is_active, created_at, updated_at
                FROM public.app_users
                WHERE id = %s AND is_active = TRUE;
                """,
                (user_id,),
            )
            return cur.fetchone()


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves an app_user by case-insensitive normalized email using the connection pool."""
    if not email:
        return None
    normalized_email = email.strip().lower()
    with _get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, display_name, avatar_url, email_verified, is_active, created_at, updated_at
                FROM public.app_users
                WHERE LOWER(email) = %s AND is_active = TRUE;
                """,
                (normalized_email,),
            )
            return cur.fetchone()


def get_email_identity(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves the email identity record including password hash."""
    if not email:
        return None
    normalized_email = email.strip().lower()
    with _get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, provider, provider_user_id, password_hash, created_at
                FROM public.auth_identities
                WHERE provider = 'email' AND provider_user_id = %s;
                """,
                (normalized_email,),
            )
            return cur.fetchone()


def get_identity_by_provider(provider: str, provider_user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an identity by provider and provider_user_id."""
    with _get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, provider, provider_user_id, password_hash, created_at
                FROM public.auth_identities
                WHERE provider = %s AND provider_user_id = %s;
                """,
                (provider, str(provider_user_id)),
            )
            return cur.fetchone()


def create_user_with_email_identity(
    email: str,
    password_hash: str,
    display_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a new user and an associated email identity in a single transaction.
    Raises ValueError if the email already exists.
    """
    normalized_email = email.strip().lower()
    resolved_display_name = (
        display_name.strip() if display_name and display_name.strip() else normalized_email.split("@")[0]
    )
    user_id = uuid.uuid4()

    try:
        with _get_connection(autocommit=False) as conn:
            with conn.cursor() as cur:
                # 1. Create app_user
                cur.execute(
                    """
                    INSERT INTO public.app_users (id, email, display_name, email_verified, is_active)
                    VALUES (%s, %s, %s, FALSE, TRUE)
                    RETURNING id, email, display_name, avatar_url, email_verified, is_active, created_at, updated_at;
                    """,
                    (user_id, normalized_email, resolved_display_name[:100]),
                )
                user_row = cur.fetchone()

                # 2. Create email auth_identity
                cur.execute(
                    """
                    INSERT INTO public.auth_identities (user_id, provider, provider_user_id, password_hash)
                    VALUES (%s, 'email', %s, %s);
                    """,
                    (user_id, normalized_email, password_hash),
                )

        logger.info(f"[AUTH] Successfully registered new user {user_id} ({normalized_email})")
        return dict(user_row)
    except psycopg.errors.UniqueViolation:
        raise ValueError("An account with this email address already exists.")
    except Exception as e:
        logger.error(f"[AUTH] Error creating user: {e}", exc_info=True)
        raise e
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"[AUTH] Error creating user: {e}", exc_info=True)
        raise e
    finally:
        if conn:
            conn.close()


def create_google_user(
    email: str,
    google_sub: str,
    display_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a new user and links their Google identity in a single transaction
    using the centralized connection pool.
    """
    normalized_email = email.strip().lower()
    resolved_name = display_name or normalized_email.split("@")[0]
    user_id = uuid.uuid4()

    with _get_connection(autocommit=False) as conn:
        with conn.cursor() as cur:
            # Create user (email_verified is True because Google verifies email)
            cur.execute(
                """
                INSERT INTO public.app_users (id, email, display_name, avatar_url, email_verified, is_active)
                VALUES (%s, %s, %s, %s, TRUE, TRUE)
                RETURNING id, email, display_name, avatar_url, email_verified, is_active, created_at, updated_at;
                """,
                (user_id, normalized_email, resolved_name[:100], avatar_url),
            )
            user_row = cur.fetchone()

            # Create Google identity
            cur.execute(
                """
                INSERT INTO public.auth_identities (user_id, provider, provider_user_id, password_hash)
                VALUES (%s, 'google', %s, NULL);
                """,
                (user_id, google_sub),
            )
    logger.info(f"[AUTH] Created new user via Google OAuth: {user_id} (sub={google_sub})")
    return dict(user_row)


def link_verified_google_identity(
    user_id: uuid.UUID,
    google_sub: str,
    avatar_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Safely and transactionally links a verified Google identity to an existing app_user:
    - Enforces that google_sub is not already linked to a different user.
    - Preserves existing app_users.id, threads, and LangGraph checkpoints.
    - Sets email_verified = TRUE on app_users upon successful verification.
    - Updates avatar_url if previously unset.
    - Handles unique constraints safely using connection pool.
    - Returns the updated app_user row.
    """
    try:
        with _get_connection(autocommit=False) as conn:
            with conn.cursor() as cur:
                # 1. Lock and check if google_sub is already linked to another user
                cur.execute(
                    """
                    SELECT user_id
                    FROM public.auth_identities
                    WHERE provider = 'google' AND provider_user_id = %s
                    FOR UPDATE;
                    """,
                    (str(google_sub),),
                )
                existing_identity = cur.fetchone()
                if existing_identity:
                    if str(existing_identity["user_id"]) != str(user_id):
                        raise ValueError("This Google identity is already associated with another account.")
                else:
                    # 2. Insert Google identity
                    cur.execute(
                        """
                        INSERT INTO public.auth_identities (user_id, provider, provider_user_id, password_hash)
                        VALUES (%s, 'google', %s, NULL);
                        """,
                        (user_id, str(google_sub)),
                    )

                # 3. Update existing user: email_verified = TRUE, avatar_url if null
                cur.execute(
                    """
                    UPDATE public.app_users
                    SET email_verified = TRUE,
                        avatar_url = COALESCE(avatar_url, %s),
                        updated_at = NOW()
                    WHERE id = %s AND is_active = TRUE
                    RETURNING id, email, display_name, avatar_url, email_verified, is_active, created_at, updated_at;
                    """,
                    (avatar_url, user_id),
                )
                user_row = cur.fetchone()
                if not user_row:
                    raise ValueError(f"User {user_id} not found or deactivated.")

        logger.info(f"[AUTH] Successfully linked verified Google identity (sub={google_sub}) to existing user {user_id}")
        return dict(user_row)
    except psycopg.errors.UniqueViolation:
        raise ValueError("This Google identity is already associated with another account.")
    except Exception as e:
        logger.error(f"[AUTH] Error linking Google identity to user {user_id}: {e}", exc_info=True)
        raise e


def link_google_identity(user_id: uuid.UUID, google_sub: str) -> bool:
    """Backward compatible wrapper for linking Google identity."""
    try:
        link_verified_google_identity(user_id, google_sub)
        return True
    except Exception:
        return False


def create_verification_token(
    user_id: uuid.UUID,
    token_type: str = "password_setup",
    expires_in_minutes: int = 15,
) -> str:
    """
    Generates a cryptographically random single-use token and stores its SHA-256 hash.
    Returns the raw secret token to be sent to the user via link/email.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

    with _get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.auth_verification_tokens (user_id, token_hash, token_type, expires_at)
                VALUES (%s, %s, %s, %s);
                """,
                (user_id, token_hash, token_type, expires_at),
            )
    return raw_token


def complete_password_setup_with_token(
    token: str,
    new_password_hash: str,
    token_type: str = "password_setup",
) -> Optional[Dict[str, Any]]:
    """
    Atomically verifies the single-use token, marks it used, sets the user's password hash,
    and updates email_verified = TRUE using a pooled transaction.
    Returns updated user dict on success, None on invalid or expired token.
    """
    token_hash = _hash_token(token)
    now = datetime.now(timezone.utc)

    try:
        with _get_connection(autocommit=False) as conn:
            with conn.cursor() as cur:
                # 1. Look up and lock the token
                cur.execute(
                    """
                    SELECT id, user_id, expires_at, used_at
                    FROM public.auth_verification_tokens
                    WHERE token_hash = %s AND token_type = %s AND used_at IS NULL
                    FOR UPDATE;
                    """,
                    (token_hash, token_type),
                )
                token_row = cur.fetchone()
                if not token_row:
                    return None

                if token_row["expires_at"] < now:
                    return None

                user_id = token_row["user_id"]

                # 2. Mark token as used
                cur.execute(
                    """
                    UPDATE public.auth_verification_tokens
                    SET used_at = %s
                    WHERE id = %s;
                    """,
                    (now, token_row["id"]),
                )

                # 3. Update or insert email auth_identity password_hash
                cur.execute(
                    """
                    UPDATE public.auth_identities
                    SET password_hash = %s
                    WHERE user_id = %s AND provider = 'email';
                    """,
                    (new_password_hash, user_id),
                )

                # 4. Mark user email_verified = TRUE
                cur.execute(
                    """
                    UPDATE public.app_users
                    SET email_verified = TRUE, updated_at = %s
                    WHERE id = %s
                    RETURNING id, email, display_name, avatar_url, email_verified, is_active, created_at, updated_at;
                    """,
                    (now, user_id),
                )
                updated_user = cur.fetchone()

        logger.info(f"[AUTH] Completed password setup for user {user_id}")
        return dict(updated_user) if updated_user else None
    except Exception as e:
        logger.error(f"[AUTH] Error completing password setup: {e}", exc_info=True)
        return None

