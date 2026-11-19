import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import jwt
from Multi_Agent_TourAI.auth.models import AuthenticatedUser
from Multi_Agent_TourAI.utils import get_logger

load_dotenv()

logger = get_logger("Multi_Agent_TourAI.auth.jwt_service")


class JwtVerificationError(Exception):
    """Raised when application JWT verification fails."""
    pass


def get_jwt_secret() -> str:
    """
    Retrieves and validates the application JWT secret key.
    Fails fast if APP_JWT_SECRET or JWT_SECRET is not configured or empty.
    Never uses an ephemeral in-memory fallback.
    """
    secret = os.getenv("APP_JWT_SECRET") or os.getenv("JWT_SECRET")
    if not secret or not secret.strip():
        raise RuntimeError(
            "APP_JWT_SECRET environment variable is missing or empty. "
            "A secure secret (minimum 32 characters) must be configured in your environment."
        )
    return secret.strip()


def get_jwt_algorithm() -> str:
    """Retrieves the allowed JWT signing algorithm (defaults to HS256)."""
    return os.getenv("APP_JWT_ALGORITHM", "HS256")


def get_jwt_issuer() -> str:
    """Retrieves the expected JWT issuer claim."""
    return os.getenv("APP_JWT_ISSUER", "multi-agent-tourai")


def get_jwt_audience() -> str:
    """Retrieves the expected JWT audience claim."""
    return os.getenv("APP_JWT_AUDIENCE", "tourai-users")


def get_token_expire_minutes() -> int:
    """Retrieves access token expiration window in minutes."""
    try:
        val = int(os.getenv("APP_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        if val <= 0:
            raise ValueError
        return val
    except ValueError:
        logger.warning("Invalid APP_ACCESS_TOKEN_EXPIRE_MINUTES, defaulting to 15 minutes.")
        return 15


def validate_jwt_configuration() -> None:
    """
    Validates JWT configuration at startup.
    Ensures secret is present and meets security standards.
    """
    secret = get_jwt_secret()
    if len(secret) < 32:
        logger.warning(
            f"APP_JWT_SECRET is shorter than 32 characters ({len(secret)} chars). "
            "For HS256, a minimum 256-bit (32 character) secret is strongly recommended."
        )


# Validate configuration on module import if environment is loaded
try:
    validate_jwt_configuration()
except RuntimeError as e:
    logger.warning(f"JWT configuration check: {e}")


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    session_id: Optional[uuid.UUID] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a signed application access JWT.
    Claims: sub (user_id UUID), email, sid (session_id), iss, aud, iat, exp, nbf.
    """
    now = datetime.now(timezone.utc)
    expire_minutes = get_token_expire_minutes()
    expire = now + (expires_delta or timedelta(minutes=expire_minutes))

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email.strip().lower(),
        "iss": get_jwt_issuer(),
        "aud": get_jwt_audience(),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if session_id:
        payload["sid"] = str(session_id)

    token = jwt.encode(payload, get_jwt_secret(), algorithm=get_jwt_algorithm())
    return token


def verify_access_token(token: str) -> AuthenticatedUser:
    """
    Cryptographically verifies an application access JWT.
    Enforces HS256 algorithm allowlist, signature, expiration, issuer, and audience.
    Never trusts client unverified identity.
    """
    if not token or not token.strip():
        raise JwtVerificationError("Token is missing or empty.")

    algorithm = get_jwt_algorithm()
    issuer = get_jwt_issuer()
    audience = get_jwt_audience()
    secret = get_jwt_secret()

    try:
        payload = jwt.decode(
            token.strip(),
            secret,
            algorithms=[algorithm],
            issuer=issuer,
            audience=audience,
            options={
                "require": ["sub", "iss", "aud", "exp", "iat"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )
    except jwt.ExpiredSignatureError:
        raise JwtVerificationError("Access token has expired.")
    except jwt.InvalidAlgorithmError:
        raise JwtVerificationError("Invalid token algorithm.")
    except jwt.InvalidIssuerError:
        raise JwtVerificationError("Invalid token issuer.")
    except jwt.InvalidAudienceError:
        raise JwtVerificationError("Invalid token audience.")
    except jwt.PyJWTError as e:
        raise JwtVerificationError(f"Token validation failed: {str(e)}")

    sub = payload.get("sub")
    if not sub:
        raise JwtVerificationError("Token is missing subject claim ('sub').")

    try:
        user_uuid = uuid.UUID(str(sub))
    except (ValueError, TypeError):
        raise JwtVerificationError("Invalid subject claim format in token.")

    email = str(payload.get("email", "")).strip().lower()
    sid_str = payload.get("sid")
    session_uuid = None
    if sid_str:
        try:
            session_uuid = uuid.UUID(str(sid_str))
        except (ValueError, TypeError):
            session_uuid = None

    return AuthenticatedUser(
        id=user_uuid,
        email=email,
        session_id=session_uuid,
        role="authenticated",
    )


__all__ = [
    "JwtVerificationError",
    "get_jwt_secret",
    "get_jwt_algorithm",
    "get_jwt_issuer",
    "get_jwt_audience",
    "get_token_expire_minutes",
    "validate_jwt_configuration",
    "create_access_token",
    "verify_access_token",
]
