import re
from typing import Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from Multi_Agent_TourAI.utils import get_logger

logger = get_logger("Multi_Agent_TourAI.auth.password_service")

# Argon2id hasher with recommended security parameters
_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validates password strength.
    Requires minimum 8 characters, maximum 128 characters, at least one letter, and at least one digit or symbol.
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[\d\W]", password):
        return False, "Password must contain at least one number or special character."
    return True, ""


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using Argon2id.
    Never logs or persists plaintext password.
    """
    valid, reason = validate_password(password)
    if not valid:
        raise ValueError(reason)
    return _hasher.hash(password)


def verify_password(hash_str: str, password: str) -> bool:
    """
    Verifies a plaintext password against an Argon2id hash in constant-time.
    Returns False if hash is invalid or password does not match.
    """
    if not hash_str or not password:
        return False
    try:
        return _hasher.verify(hash_str, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception as e:
        logger.error(f"[AUTH] Unexpected error during password verification: {e}")
        return False

