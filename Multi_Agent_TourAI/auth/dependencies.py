from fastapi import Request, HTTPException, Depends, status
from Multi_Agent_TourAI.auth.models import AuthenticatedUser
from Multi_Agent_TourAI.auth.jwt_service import verify_access_token, JwtVerificationError
from Multi_Agent_TourAI.auth.rate_limiter import get_rate_limiter
from Multi_Agent_TourAI.utils import get_logger

logger = get_logger("Multi_Agent_TourAI.auth.dependencies")


async def get_current_user(request: Request) -> AuthenticatedUser:
    """
    Extracts and cryptographically verifies the application Bearer JWT from
    the HTTP Authorization header.
    Never accepts client unverified user_ids.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = auth_header.strip().split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        user = verify_access_token(token)
        return user
    except JwtVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user(request: Request) -> AuthenticatedUser | None:
    """
    Returns the authenticated user if a valid token is present, otherwise None.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    try:
        parts = auth_header.strip().split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return verify_access_token(parts[1])
    except Exception:
        pass
    return None


def check_rate_limit_for(endpoint_type: str):
    """
    Dependency factory to enforce sliding window rate limits per authenticated user.
    """
    async def _rate_limit_dep(user: AuthenticatedUser = Depends(get_current_user)):
        limiter = get_rate_limiter()
        is_limited, retry_after = limiter.is_rate_limited(user.user_id_str, endpoint_type)
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {endpoint_type}. Please retry in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )
        return user

    return _rate_limit_dep
