from Multi_Agent_TourAI.auth.models import (
    AuthenticatedUser,
    ThreadSummary,
    AppUserPublic,
    RegisterRequest,
    LoginRequest,
    RequestPasswordSetupRequest,
    CompletePasswordSetupRequest,
    AuthResponse,
)
from Multi_Agent_TourAI.auth.jwt_service import (
    create_access_token,
    verify_access_token,
    JwtVerificationError,
)
from Multi_Agent_TourAI.auth.password_service import (
    hash_password,
    verify_password,
    validate_password,
)
from Multi_Agent_TourAI.auth.thread_repo import (
    create_user_thread,
    verify_thread_ownership,
    get_user_threads,
    safe_delete_user_thread,
)
from Multi_Agent_TourAI.auth.dependencies import (
    get_current_user,
    get_optional_current_user,
    check_rate_limit_for,
)
from Multi_Agent_TourAI.auth.session_service import (
    create_session,
    rotate_session,
    revoke_session_by_token,
    revoke_all_user_sessions,
    set_refresh_cookie,
    clear_refresh_cookie,
    RefreshTokenReusedError,
    RefreshTokenRecentlyRotatedError,
)
from Multi_Agent_TourAI.auth.google_oauth import (
    generate_google_auth_url,
    process_google_callback,
)

__all__ = [
    "AuthenticatedUser",
    "ThreadSummary",
    "AppUserPublic",
    "RegisterRequest",
    "LoginRequest",
    "RequestPasswordSetupRequest",
    "CompletePasswordSetupRequest",
    "AuthResponse",
    "create_access_token",
    "verify_access_token",
    "JwtVerificationError",
    "hash_password",
    "verify_password",
    "validate_password",
    "create_user_thread",
    "verify_thread_ownership",
    "get_user_threads",
    "safe_delete_user_thread",
    "get_current_user",
    "get_optional_current_user",
    "check_rate_limit_for",
    "create_session",
    "rotate_session",
    "revoke_session_by_token",
    "revoke_all_user_sessions",
    "set_refresh_cookie",
    "clear_refresh_cookie",
    "RefreshTokenReusedError",
    "RefreshTokenRecentlyRotatedError",
    "generate_google_auth_url",
    "process_google_callback",
]
