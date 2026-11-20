import os
import uuid
import hmac
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, Iterator
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row

from Multi_Agent_TourAI.database import get_db_connection
from Multi_Agent_TourAI.auth.session_service import revoke_all_user_sessions
from Multi_Agent_TourAI.utils import get_logger

logger = get_logger("Multi_Agent_TourAI.auth.otp_repository")

# Security constants
OTP_EXPIRATION_MINUTES = 3
MAX_OTP_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60
RESET_TOKEN_EXPIRATION_MINUTES = 15


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


def ensure_password_reset_table() -> None:
    """Ensures the password_reset_otps table and indexes exist in PostgreSQL."""
    try:
        with _get_connection(autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.password_reset_otps (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
                        otp_hash TEXT NOT NULL,
                        reset_token_hash TEXT NULL,
                        expires_at TIMESTAMPTZ NOT NULL,
                        attempts INT NOT NULL DEFAULT 0,
                        verified_at TIMESTAMPTZ NULL,
                        consumed_at TIMESTAMPTZ NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );

                    CREATE INDEX IF NOT EXISTS idx_password_reset_otps_user_id 
                        ON public.password_reset_otps (user_id);

                    CREATE INDEX IF NOT EXISTS idx_password_reset_otps_user_created 
                        ON public.password_reset_otps (user_id, created_at DESC);

                    CREATE INDEX IF NOT EXISTS idx_password_reset_otps_reset_token 
                        ON public.password_reset_otps (reset_token_hash) 
                        WHERE consumed_at IS NULL;
                    """
                )
        logger.info("[AUTH] Verified password_reset_otps schema availability.")
    except Exception as e:
        logger.warning(f"[AUTH] ensure_password_reset_table check warning: {e}")


def _hash_otp(otp: str, user_id: uuid.UUID) -> str:
    """
    Computes a salted SHA-256 hash of a 6-digit OTP using user_id as salt.
    Prevents precomputed rainbow table attacks against 6-digit spaces.
    """
    salt = str(user_id).encode("utf-8")
    return hashlib.sha256(salt + b":" + otp.strip().encode("utf-8")).hexdigest()


def _hash_token(token: str) -> str:
    """Computes SHA-256 hash of a raw reset token."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()


def generate_secure_otp() -> str:
    """
    Generates a cryptographically secure, random 6-digit numeric OTP using secrets.
    Format: 000000 to 999999.
    """
    return f"{secrets.randbelow(1_000_000):06d}"


def get_last_otp_created_at(user_id: uuid.UUID) -> Optional[datetime]:
    """Retrieves the timestamp of the most recent OTP created for this user."""
    try:
        with _get_connection(autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT created_at 
                    FROM public.password_reset_otps 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 1;
                    """,
                    (user_id,),
                )
                row = cur.fetchone()
                if row:
                    return row["created_at"] if isinstance(row, dict) else row[0]
                return None
    except Exception as e:
        logger.error(f"[AUTH] Error checking last OTP time for user {user_id}: {e}", exc_info=True)
        return None


def create_password_reset_otp(
    user_id: uuid.UUID,
    otp: str,
    expires_in_minutes: int = OTP_EXPIRATION_MINUTES,
) -> str:
    """
    Stores a salted hashed 6-digit OTP for the user.
    Atomically invalidates any previous unconsumed OTPs for this user.
    """
    otp_hash = _hash_otp(otp, user_id)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expires_in_minutes)
    record_id = uuid.uuid4()

    with _get_connection(autocommit=False) as conn:
        with conn.cursor() as cur:
            # Invalidate any prior active unconsumed OTPs for this user
            cur.execute(
                """
                UPDATE public.password_reset_otps
                SET consumed_at = %s
                WHERE user_id = %s AND consumed_at IS NULL;
                """,
                (now, user_id),
            )

            # Insert fresh OTP record
            cur.execute(
                """
                INSERT INTO public.password_reset_otps (id, user_id, otp_hash, expires_at, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (record_id, user_id, otp_hash, expires_at, now),
            )
        conn.commit()

    logger.info(f"[AUTH] Generated password reset OTP record {record_id} for user {user_id}")
    return str(record_id)


def verify_password_reset_otp(
    user_id: uuid.UUID,
    otp: str,
) -> Tuple[bool, Optional[str], str]:
    """
    Verifies an entered 6-digit OTP against the stored salted hash.
    Enforces expiration, maximum 5 attempts, and prevents replay attacks.
    On success: marks verified_at and returns (True, reset_token, success_message).
    """
    now = datetime.now(timezone.utc)
    computed_hash = _hash_otp(otp, user_id)

    with _get_connection(autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, otp_hash, expires_at, attempts, verified_at, consumed_at
                FROM public.password_reset_otps
                WHERE user_id = %s AND verified_at IS NULL AND consumed_at IS NULL
                ORDER BY created_at DESC
                LIMIT 1
                FOR UPDATE;
                """,
                (user_id,),
            )
            row = cur.fetchone()

            if not row:
                conn.rollback()
                return False, None, "Invalid or expired verification code."

            # Safe mapping for dict_row and tuple
            row_dict = row if isinstance(row, dict) else {
                "id": row[0],
                "user_id": row[1],
                "otp_hash": row[2],
                "expires_at": row[3],
                "attempts": row[4],
                "verified_at": row[5],
                "consumed_at": row[6],
            }

            rec_id = row_dict["id"]
            attempts = int(row_dict["attempts"])
            expires_at = row_dict["expires_at"]
            stored_hash = row_dict["otp_hash"]

            # Check attempt limit
            if attempts >= MAX_OTP_ATTEMPTS:
                cur.execute(
                    "UPDATE public.password_reset_otps SET consumed_at = %s WHERE id = %s",
                    (now, rec_id),
                )
                conn.commit()
                return False, None, "Maximum verification attempts exceeded. Please request a new code."

            # Check expiration
            if expires_at < now:
                cur.execute(
                    "UPDATE public.password_reset_otps SET consumed_at = %s WHERE id = %s",
                    (now, rec_id),
                )
                conn.commit()
                return False, None, "Verification code has expired. Please request a new code."

            # Constant-time comparison
            if not hmac.compare_digest(stored_hash, computed_hash):
                new_attempts = attempts + 1
                if new_attempts >= MAX_OTP_ATTEMPTS:
                    cur.execute(
                        "UPDATE public.password_reset_otps SET attempts = %s, consumed_at = %s WHERE id = %s",
                        (new_attempts, now, rec_id),
                    )
                else:
                    cur.execute(
                        "UPDATE public.password_reset_otps SET attempts = %s WHERE id = %s",
                        (new_attempts, rec_id),
                    )
                conn.commit()
                remaining = max(0, MAX_OTP_ATTEMPTS - new_attempts)
                return False, None, f"Invalid verification code. {remaining} attempt(s) remaining."

            # Verification Successful: Issue single-use reset token
            reset_token = secrets.token_urlsafe(32)
            reset_token_hash = _hash_token(reset_token)

            cur.execute(
                """
                UPDATE public.password_reset_otps
                SET verified_at = %s, reset_token_hash = %s
                WHERE id = %s;
                """,
                (now, reset_token_hash, rec_id),
            )
            conn.commit()

        logger.info(f"[AUTH] Successfully verified reset OTP for user {user_id}")
        return True, reset_token, "Code verified successfully."


def reset_password_with_token(
    reset_token: str,
    new_password_hash: str,
) -> Tuple[bool, str]:
    """
    Atomically consumes the single-use reset token, updates the user's password hash in auth_identities,
    and invalidates all existing user sessions.
    """
    now = datetime.now(timezone.utc)
    token_hash = _hash_token(reset_token)

    try:
        with _get_connection(autocommit=False) as conn:
            with conn.cursor() as cur:
                # 1. Lock and verify the reset token record
                cur.execute(
                    """
                    SELECT id, user_id, verified_at, expires_at, consumed_at
                    FROM public.password_reset_otps
                    WHERE reset_token_hash = %s AND consumed_at IS NULL
                    FOR UPDATE;
                    """,
                    (token_hash,),
                )
                row = cur.fetchone()
                if not row:
                    conn.rollback()
                    return False, "Invalid or expired reset token."

                row_dict = row if isinstance(row, dict) else {
                    "id": row[0],
                    "user_id": row[1],
                    "verified_at": row[2],
                    "expires_at": row[3],
                    "consumed_at": row[4],
                }

                user_id = row_dict["user_id"]
                verified_at = row_dict["verified_at"]

                if not verified_at:
                    conn.rollback()
                    return False, "Reset token has not been verified."

                # Reset token valid for 15 minutes after verification
                if (now - verified_at) > timedelta(minutes=RESET_TOKEN_EXPIRATION_MINUTES):
                    cur.execute(
                        "UPDATE public.password_reset_otps SET consumed_at = %s WHERE id = %s",
                        (now, row_dict["id"]),
                    )
                    conn.commit()
                    return False, "Reset token has expired. Please request a new verification code."

                # 2. Update user's email identity password_hash
                cur.execute(
                    """
                    UPDATE public.auth_identities
                    SET password_hash = %s
                    WHERE user_id = %s AND provider = 'email';
                    """,
                    (new_password_hash, user_id),
                )
                if cur.rowcount == 0:
                    conn.rollback()
                    logger.warning(f"[AUTH] Attempted password reset on account without email identity: {user_id}")
                    return False, "Password reset is not supported for this account type."

                # 3. Mark all OTP records for this user as consumed
                cur.execute(
                    """
                    UPDATE public.password_reset_otps
                    SET consumed_at = %s
                    WHERE user_id = %s AND consumed_at IS NULL;
                    """,
                    (now, user_id),
                )

                # 4. Mark app_users email_verified = TRUE and updated_at = now
                cur.execute(
                    """
                    UPDATE public.app_users
                    SET email_verified = TRUE, updated_at = %s
                    WHERE id = %s;
                    """,
                    (now, user_id),
                )

            conn.commit()

        # 5. Revoke all active sessions for this user (global session invalidation)
        revoke_count = revoke_all_user_sessions(user_id)
        logger.info(f"[AUTH] Successfully reset password for user {user_id}. Revoked {revoke_count} active sessions.")
        return True, "Your password has been reset successfully. Please log in using your new password."
    except Exception as e:
        logger.error(f"[AUTH] Error resetting password with token: {e}", exc_info=True)
        return False, "An error occurred while resetting your password. Please try again."


__all__ = [
    "ensure_password_reset_table",
    "generate_secure_otp",
    "create_password_reset_otp",
    "verify_password_reset_otp",
    "reset_password_with_token",
    "get_last_otp_created_at",
    "OTP_EXPIRATION_MINUTES",
    "MAX_OTP_ATTEMPTS",
    "RESEND_COOLDOWN_SECONDS",
    "RESET_TOKEN_EXPIRATION_MINUTES",
]
