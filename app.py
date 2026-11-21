import os
import re
import time
import json
import uuid
import asyncio
import uvicorn
import urllib.parse
from datetime import datetime, timezone
from typing import Any
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import nest_asyncio
from fastapi.responses import StreamingResponse, RedirectResponse
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from fastapi import FastAPI, HTTPException, Depends, Response, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from Multi_Agent_TourAI.graph.workflow import travel_graph, run_travel_agent, resume_travel_agent
from Multi_Agent_TourAI.guardrails.inputguardrail import check_input_safety
from Multi_Agent_TourAI.guardrails.outputguardrail import sanitize_text
from Multi_Agent_TourAI.auth import (
    AuthenticatedUser,
    get_current_user,
    get_optional_current_user,
    check_rate_limit_for,
    create_user_thread,
    verify_thread_ownership,
    get_user_threads,
    safe_delete_user_thread,
    RegisterRequest,
    LoginRequest,
    RequestPasswordSetupRequest,
    CompletePasswordSetupRequest,
    AuthResponse,
    AppUserPublic,
    create_access_token,
    hash_password,
    verify_password,
    validate_password,
    create_session,
    rotate_session,
    revoke_session_by_token,
    revoke_all_user_sessions,
    set_refresh_cookie,
    clear_refresh_cookie,
    RefreshTokenReusedError,
    RefreshTokenRecentlyRotatedError,
    generate_google_auth_url,
    process_google_callback,
    ValidateResetEmailRequest,
    ValidateResetEmailResponse,
    CheckEmailRequest,
    CheckEmailResponse,
    ForgotPasswordRequest,
    VerifyResetOtpRequest,
    ResendResetOtpRequest,
    ResetPasswordRequest,
    VerifyOtpResponse,
    GenericMessageResponse,
    check_password_reset_eligibility,
    ensure_password_reset_table,
    generate_secure_otp,
    create_password_reset_otp,
    verify_password_reset_otp,
    reset_password_with_token,
    get_last_otp_created_at,
    OTP_EXPIRATION_MINUTES,
    RESEND_COOLDOWN_SECONDS,
    send_password_reset_email,
    send_oauth_account_notice_email,
)
from Multi_Agent_TourAI.auth.rate_limiter import get_rate_limiter
from Multi_Agent_TourAI.auth.auth_repository import (
    get_user_by_email,
    get_user_by_id,
    get_email_identity,
    create_user_with_email_identity,
    create_verification_token,
    complete_password_setup_with_token,
)
from Multi_Agent_TourAI.utils import (
    get_logger,
    get_request_id,
    set_request_id,
    reset_request_id,
    mask_email,
    pseudonymize_id,
)
from Multi_Agent_TourAI.database import (
    get_connection_pool,
    close_connection_pool,
    check_database_health,
)

logger = get_logger("Multi_Agent_TourAI.api")

if os.getenv("ENABLE_NEST_ASYNCIO", "false").lower() in ("true", "1"):
    try:
        nest_asyncio.apply()
    except Exception as e:
        logger.warning(f"Failed to apply nest_asyncio: {e}")

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager:
    - Pre-warms and verifies the PostgreSQL connection pool on startup.
    - Gracefully drains and closes all database pool connections on shutdown.
    """
    logger.info("[LIFESPAN] Starting up Multi_Agent_TourAI backend. Initializing DB connection pool...")
    try:
        get_connection_pool()
        health = check_database_health()
        logger.info(f"[LIFESPAN] Database connection pool healthy: {health}")
        ensure_password_reset_table()
    except Exception as e:
        logger.error(f"[LIFESPAN] Warning: Database pool initialization check encountered an issue: {e}")
    
    yield

    logger.info("[LIFESPAN] Shutting down Multi_Agent_TourAI backend. Draining database connection pool...")
    try:
        close_connection_pool()
        logger.info("[LIFESPAN] Database connection pool closed successfully.")
    except Exception as e:
        logger.warning(f"[LIFESPAN] Error during database connection pool shutdown: {e}")


# fastapi app
app = FastAPI(
    title = "Multi_Agent_TourAI API",
    description= "Backend API for LangGraph Travel Planner with Human-in-the-Loop",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Middleware - Enforce explicit allowed origins without wildcards
_frontend_origins_env = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_allowed_origins = [orig.strip() for orig in _frontend_origins_env.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Request ID & Lifecycle Logging Middleware
_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """
    Intercepts incoming HTTP requests to:
    - Validate or generate a unique X-Request-ID (UUIDv4).
    - Store the request_id in contextvars for downstream logger propagation.
    - Measure request execution latency.
    - Log request completion safely without logging sensitive bodies, headers, or query params.
    - Return X-Request-ID header to client.
    """
    incoming_id = request.headers.get("X-Request-ID", "").strip()
    if incoming_id and _REQUEST_ID_REGEX.match(incoming_id):
        req_id = incoming_id
    else:
        req_id = str(uuid.uuid4())

    token = set_request_id(req_id)
    start_time = time.time()
    path = request.url.path

    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Request-ID"] = req_id

        # Skip high-frequency health check spam unless it fails
        if path != "/health" or response.status_code >= 400:
            logger.info(
                f"HTTP {request.method} {path} - status={response.status_code} duration={duration_ms:.2f}ms"
            )
        return response
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"HTTP {request.method} {path} failed after {duration_ms:.2f}ms | Error: {type(exc).__name__}: {str(exc)}",
            exc_info=True
        )
        raise exc
    finally:
        reset_request_id(token)

# Request , Response data models
class TravelRequest(BaseModel):
    query: str = Field(..., max_length=1500, examples=["Plan a 5 days trip to Dubai from Sri Lanka"])
    thread_id: str | None = Field(default=None, max_length=100, examples=["user_session_123"])

class ResumeRequest(BaseModel):
    thread_id: str = Field(..., max_length=100, examples=["user_session_123"])
    approved: bool = Field(..., examples=[True])
    feedback: str = Field(default="", max_length=1500, examples=["Please add more budget-friendly hotel options."])

class TravelResponse(BaseModel):
    thread_id: str
    answer: str
    requires_approval: bool = False
    approval_request: str | None = ""
    flight_results: str | None = ""
    hotel_results: str | None = ""
    weather_results: str | None = ""
    maps_results: str | None = ""
    itinerary: str | None = ""
    approved: bool | None = None
    human_feedback: str | None = ""
    llm_calls: int = 0
    guardrail_allowed: bool | None = True
    output_guardrail_passed: bool | None = True
    output_guardrail_reason: str | None = ""


# Internal Helpers & Constants
_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _to_public_user(user_dict: dict) -> AppUserPublic:
    """Safely maps a database user row/dict to the public AppUserPublic schema."""
    return AppUserPublic(
        id=str(user_dict["id"]),
        email=user_dict["email"],
        display_name=user_dict.get("display_name"),
        avatar_url=user_dict.get("avatar_url"),
        email_verified=user_dict.get("email_verified", False),
        created_at=user_dict.get("created_at"),
    )


def _extract_text(raw_content: Any) -> str:
    """Extracts plain text from LangChain message content (string or list of parts)."""
    if isinstance(raw_content, list):
        return "".join(
            p if isinstance(p, str) else p.get("text", str(p))
            for p in raw_content
        )
    return str(raw_content or "")


def _build_approval_payload(thread_id: str, interrupt_source: Any, accumulated_state: dict) -> dict:
    """Constructs a sanitized HITL approval event payload."""
    interrupt_val = getattr(interrupt_source, "value", interrupt_source) if interrupt_source else {}
    payload_val = interrupt_val if isinstance(interrupt_val, dict) else {"question": str(interrupt_val)}
    raw_draft = payload_val.get("draft_itinerary") or accumulated_state.get("itinerary", "")
    sanitized_draft, _ = sanitize_text(raw_draft)
    return {
        "event": "approval_required",
        "thread_id": thread_id,
        "question": payload_val.get("question", "Do you approve this draft itinerary?"),
        "draft_itinerary": sanitized_draft,
        "llm_calls": accumulated_state.get("llm_calls", 0),
    }


async def _stream_token_chunks(text: str):
    """Yields token events word-by-word with realistic typewriter pacing."""
    tokens = re.findall(r"\S+|\s+", text)
    for token in tokens:
        yield f"data: {json.dumps({'event': 'token', 'token': token})}\n\n"
        await asyncio.sleep(0.015)


# API endpoints
@app.get("/health")
async def health_check():
    db_health = check_database_health()
    is_healthy = db_health.get("status") == "healthy"
    return {
        "status": "healthy" if is_healthy else "degraded",
        "services": "Multi_Agent_TourAI",
        "database": db_health,
    }


# Authentication Endpoints 

@app.post("/api/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def auth_register(payload: RegisterRequest, response: Response):
    valid, reason = validate_password(payload.password)
    if not valid:
        raise HTTPException(status_code=400, detail=reason)

    pwd_hash = hash_password(payload.password)
    try:
        user_row = create_user_with_email_identity(
            email=payload.email,
            password_hash=pwd_hash,
            display_name=payload.display_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    user_id = user_row["id"]
    session_id, raw_refresh_token = create_session(user_id)
    set_refresh_cookie(response, raw_refresh_token)
    access_token = create_access_token(user_id, user_row["email"], session_id=session_id)

    return AuthResponse(
        access_token=access_token,
        user=_to_public_user(user_row),
    )


@app.post("/api/auth/login", response_model=AuthResponse)
async def auth_login(payload: LoginRequest, response: Response):
    email = payload.email.strip().lower()
    user_row = get_user_by_email(email)
    identity = get_email_identity(email)

    invalid_creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user_row or not identity:
        raise invalid_creds_exc

    # Check if this is an existing migrated user requiring initial password setup
    if identity.get("password_hash") is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CREDENTIAL_SETUP_REQUIRED: Initial password setup is required for this account. Please request a verification link.",
        )

    if not verify_password(identity["password_hash"], payload.password):
        raise invalid_creds_exc

    user_id = user_row["id"]
    session_id, raw_refresh_token = create_session(user_id)
    set_refresh_cookie(response, raw_refresh_token, remember_me=payload.remember_me if payload.remember_me is not None else True)
    access_token = create_access_token(user_id, user_row["email"], session_id=session_id)

    return AuthResponse(
        access_token=access_token,
        user=_to_public_user(user_row),
    )


@app.post("/api/auth/request-password-setup")
async def auth_request_password_setup(payload: RequestPasswordSetupRequest):
    email = payload.email.strip().lower()
    user_row = get_user_by_email(email)

    if user_row:
        token = create_verification_token(user_row["id"], token_type="password_setup", expires_in_minutes=15)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        setup_url = f"{frontend_url}/auth/setup-password?token={token}"
        logger.info(f"[AUTH ONBOARDING] Password setup link for {email}: {setup_url}")

    return {"message": "If an account exists with this email address, a password setup link has been generated."}


@app.post("/api/auth/complete-password-setup", response_model=AuthResponse)
async def auth_complete_password_setup(payload: CompletePasswordSetupRequest, response: Response):
    valid, reason = validate_password(payload.new_password)
    if not valid:
        raise HTTPException(status_code=400, detail=reason)

    pwd_hash = hash_password(payload.new_password)
    updated_user = complete_password_setup_with_token(payload.token, pwd_hash, token_type="password_setup")
    if not updated_user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")

    user_id = updated_user["id"]
    session_id, raw_refresh_token = create_session(user_id)
    set_refresh_cookie(response, raw_refresh_token)
    access_token = create_access_token(user_id, updated_user["email"], session_id=session_id)

    return AuthResponse(
        access_token=access_token,
        user=_to_public_user(updated_user),
    )


@app.post("/api/auth/check-email", response_model=CheckEmailResponse)
async def auth_check_email(payload: CheckEmailRequest, request: Request):
    """
    Checks email registration status for real-time frontend field validation (Login & Sign Up).
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()
    is_limited, retry_after = rate_limiter.is_rate_limited(client_ip, "check_email")
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail=f"Too many validation requests. Please retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    email = payload.email.strip().lower()
    user_row = get_user_by_email(email)
    if not user_row:
        return CheckEmailResponse(
            email=email,
            exists=False,
            has_password=False,
            is_oauth=False,
            message="This email address is not registered. Please check your email or create an account.",
        )

    email_identity = get_email_identity(email)
    has_password = bool(email_identity and email_identity.get("password_hash"))
    is_oauth = not has_password

    msg = "This account is registered."
    if is_oauth:
        msg = "This account was registered with Google Sign-In and does not have a password configured. Please sign in with Google."

    return CheckEmailResponse(
        email=email,
        exists=True,
        has_password=has_password,
        is_oauth=is_oauth,
        message=msg,
    )


@app.post("/api/auth/validate-reset-email", response_model=ValidateResetEmailResponse)
async def auth_validate_reset_email(payload: ValidateResetEmailRequest, request: Request):
    """
    Step 0: Initial Email Validation for Password Reset.
    Validates email against active registered user accounts with password authentication enabled.
    Rejects unregistered emails and OAuth-only accounts without generating an OTP or sending an email.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()
    is_limited, retry_after = rate_limiter.is_rate_limited(client_ip, "forgot_password")
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail=f"Too many reset requests. Please retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    email = payload.email.strip().lower()
    is_eligible, err_msg, user_row = check_password_reset_eligibility(email)
    if not is_eligible:
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg or "This email address is not registered. Please check your email or create an account.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg or "This account is not eligible for password reset.",
        )

    return ValidateResetEmailResponse(
        valid=True,
        email=email,
        message="Email is registered and eligible for password reset.",
    )


@app.post("/api/auth/forgot-password", response_model=GenericMessageResponse)
async def auth_forgot_password(payload: ForgotPasswordRequest, request: Request):
    """
    Step 1: Request Password Reset.
    Re-validates that the email belongs to an eligible registered account with password authentication enabled.
    Generates a secure, 6-digit time-limited OTP and emails it to the registered user.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()
    is_limited, retry_after = rate_limiter.is_rate_limited(client_ip, "forgot_password")
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail=f"Too many reset requests. Please retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    email = payload.email.strip().lower()
    is_eligible, err_msg, user_row = check_password_reset_eligibility(email)
    if not is_eligible:
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg or "This email address is not registered. Please check your email or create an account.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg or "This account is not eligible for password reset.",
        )

    user_id = user_row["id"]

    # Enforce 60-second resend cooldown
    last_created = get_last_otp_created_at(user_id)
    if last_created:
        elapsed = (datetime.now(timezone.utc) - last_created).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            remaining = int(RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {remaining} seconds before requesting a new code.",
                headers={"Retry-After": str(remaining)},
            )

    otp = generate_secure_otp()
    create_password_reset_otp(user_id, otp, expires_in_minutes=OTP_EXPIRATION_MINUTES)
    email_sent = send_password_reset_email(email, otp)
    if not email_sent:
        logger.warning(f"[AUTH] Email delivery failure for password reset to {email}")

    return GenericMessageResponse(message="A 6-digit verification code has been sent to your email.")


@app.post("/api/auth/verify-reset-otp", response_model=VerifyOtpResponse)
async def auth_verify_reset_otp(payload: VerifyResetOtpRequest, request: Request):
    """
    Step 2: Verify 6-digit OTP.
    Validates entered OTP against salted hash, enforces max 5 attempts and 5-min expiration.
    Returns a single-use cryptographically secure reset_token.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()
    is_limited, retry_after = rate_limiter.is_rate_limited(client_ip, "verify_otp")
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail=f"Too many verification attempts. Please retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    email = payload.email.strip().lower()
    user_row = get_user_by_email(email)
    if not user_row:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    user_id = user_row["id"]
    success, reset_token, message = verify_password_reset_otp(user_id, payload.otp)
    if not success or not reset_token:
        raise HTTPException(status_code=400, detail=message)

    return VerifyOtpResponse(
        message=message,
        reset_token=reset_token,
    )


@app.post("/api/auth/reset-password", response_model=GenericMessageResponse)
async def auth_reset_password(payload: ResetPasswordRequest, request: Request):
    """
    Step 3: Set New Password.
    Verifies single-use reset token, enforces password policy, updates Argon2id hash,
    and invalidates all existing user sessions.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()
    is_limited, retry_after = rate_limiter.is_rate_limited(client_ip, "reset_password")
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail=f"Too many password reset attempts. Please retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    if payload.confirm_password is not None and payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    valid, reason = validate_password(payload.new_password)
    if not valid:
        raise HTTPException(status_code=400, detail=reason)

    pwd_hash = hash_password(payload.new_password)
    success, message = reset_password_with_token(payload.reset_token, pwd_hash)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return GenericMessageResponse(message=message)


@app.post("/api/auth/resend-reset-otp", response_model=GenericMessageResponse)
async def auth_resend_reset_otp(payload: ResendResetOtpRequest, request: Request):
    """
    Resends a fresh 6-digit OTP to the registered user with independent eligibility and cooldown checks.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()
    is_limited, retry_after = rate_limiter.is_rate_limited(client_ip, "resend_otp")
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail=f"Too many resend requests. Please retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    email = payload.email.strip().lower()
    is_eligible, err_msg, user_row = check_password_reset_eligibility(email)
    if not is_eligible:
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg or "This email address is not registered. Please check your email or create an account.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg or "This account is not eligible for password reset.",
        )

    user_id = user_row["id"]
    last_created = get_last_otp_created_at(user_id)
    if last_created:
        elapsed = (datetime.now(timezone.utc) - last_created).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            remaining = int(RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {remaining} seconds before requesting a new code.",
                headers={"Retry-After": str(remaining)},
            )

    otp = generate_secure_otp()
    create_password_reset_otp(user_id, otp, expires_in_minutes=OTP_EXPIRATION_MINUTES)
    send_password_reset_email(email, otp)

    return GenericMessageResponse(message="A fresh 6-digit verification code has been sent to your email.")


@app.get("/api/auth/google")
async def auth_google_redirect():
    auth_url, state = generate_google_auth_url()
    return {"auth_url": auth_url, "state": state}


@app.get("/api/auth/google/callback")
async def auth_google_callback(code: str, state: str):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    try:
        user_row = process_google_callback(code, state)
    except Exception as e:
        logger.error(f"[AUTH] Google OAuth callback error: {e}")
        err_msg = urllib.parse.quote_plus(str(e))
        return RedirectResponse(url=f"{frontend_url}?auth_error={err_msg}")

    user_id = user_row["id"]
    session_id, raw_refresh_token = create_session(user_id)
    redirect = RedirectResponse(url=f"{frontend_url}?auth_success=true", status_code=status.HTTP_302_FOUND)
    set_refresh_cookie(redirect, raw_refresh_token)
    return redirect


@app.get("/api/auth/me")
async def auth_me(user: AuthenticatedUser = Depends(get_current_user)):
    user_row = get_user_by_id(user.id)
    if not user_row:
        raise HTTPException(status_code=404, detail="User account not found.")
    return {"user": _to_public_user(user_row)}


@app.post("/api/auth/refresh", response_model=AuthResponse)
async def auth_refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("tourai_refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token cookie missing.")

    try:
        result = rotate_session(refresh_token)
    except RefreshTokenRecentlyRotatedError:
        # Legitimate concurrent race detected within grace window.
        # Do not clear cookie (preserves winner's fresh cookie).
        # Do not issue any token (prevents malicious replay).
        raise HTTPException(
            status_code=409,
            detail="Refresh token already rotated. Please use current session.",
        )
    except RefreshTokenReusedError:
        # Malicious reuse detected outside grace window: all sessions revoked.
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=401,
            detail="Session compromised: token reuse detected. All sessions terminated.",
        )

    if not result:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Invalid, expired, or revoked refresh token.")

    user_dict, new_session_id, new_raw_token = result
    set_refresh_cookie(response, new_raw_token)
    access_token = create_access_token(user_dict["id"], user_dict["email"], session_id=new_session_id)

    return AuthResponse(
        access_token=access_token,
        user=_to_public_user(user_dict),
    )


@app.post("/api/auth/logout")
async def auth_logout(request: Request, response: Response):
    refresh_token = request.cookies.get("tourai_refresh_token")
    if refresh_token:
        revoke_session_by_token(refresh_token)
    clear_refresh_cookie(response)
    return {"status": "logged_out"}


@app.post("/api/auth/logout-all")
async def auth_logout_all(response: Response, user: AuthenticatedUser = Depends(get_current_user)):
    revoke_all_user_sessions(user.id)
    clear_refresh_cookie(response)
    return {"status": "all_sessions_revoked"}

@app.post("/api/plan", response_model=TravelResponse)
async def plan(
    payload: TravelRequest,
    user: AuthenticatedUser = Depends(check_rate_limit_for("plan")),
):
    user_query = payload.query.strip()

    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if payload.thread_id:
        if not verify_thread_ownership(user.id, payload.thread_id):
            raise HTTPException(status_code=404, detail="Thread not found")
        thread_id = payload.thread_id
    else:
        thread_id = create_user_thread(user.id, title=user_query[:50])

    logger.info(f"Incoming Travel Request | Thread: {pseudonymize_id(thread_id)} | User: {pseudonymize_id(user.id)} | QueryLength: {len(user_query)}")

    try:
        # run Multi-Agent Workflow
        result = run_travel_agent(user_input=user_query, thread_id=thread_id, user_id=user.user_id_str)
        logger.info(f"Travel Plan Ready | Requires Approval: {result.get('requires_approval', False)} | Total LLM Calls: {result.get('llm_calls', 0)}")
        return result
    except Exception as e:
        logger.error(f"Error executing Multi-Agent workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while executing the travel planning workflow.")

@app.post("/api/plan/resume", response_model=TravelResponse)
async def resume(
    payload: ResumeRequest,
    user: AuthenticatedUser = Depends(check_rate_limit_for("resume")),
):
    thread_id = payload.thread_id.strip() if payload.thread_id else ""
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required to resume workflow.")

    if not verify_thread_ownership(user.id, thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")

    feedback = payload.feedback.strip() if payload.feedback else ""
    if len(feedback) > 1500:
        raise HTTPException(status_code=400, detail="Feedback exceeds maximum length of 1500 characters.")

    # Validate feedback through input guardrail before resuming workflow
    if feedback:
        allowed, reason = check_input_safety(feedback, is_feedback=True)
        if not allowed:
            logger.warning(f"Resume feedback blocked by input guardrail | Thread: {pseudonymize_id(thread_id)} | Reason: {reason}")
            raise HTTPException(status_code=400, detail=f"Feedback rejected by safety guardrail: {reason}")

    logger.info(f"Incoming Resume Request | Thread: {pseudonymize_id(thread_id)} | User: {pseudonymize_id(user.id)} | Approved: {payload.approved} | FeedbackLength: {len(feedback)}")
    try:
        result = resume_travel_agent(
            thread_id=thread_id,
            approved=payload.approved,
            feedback=feedback,
            user_id=user.user_id_str,
        )
        logger.info(f"Workflow Resumed | Total LLM Calls: {result.get('llm_calls', 0)}")
        return result
    except ValueError as ve:
        logger.warning(f"Validation error resuming workflow: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error resuming workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while resuming the workflow.")

@app.get("/api/history/{thread_id}")
async def get_thread_history(
    thread_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    if not verify_thread_ownership(user.id, thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user.user_id_str,
        }
    }
    try:
        checkpoint_state = travel_graph.get_state(config)
        if not checkpoint_state or not checkpoint_state.values:
            return {"turns": [], "thread_id": thread_id}

        state_values = dict(checkpoint_state.values)
        messages = state_values.get("messages", [])
        flight_results = state_values.get("flight_results", "")
        hotel_results = state_values.get("hotel_results", "")
        weather_results = state_values.get("weather_results", "")
        maps_results = state_values.get("maps_results", "")
        itinerary = state_values.get("itinerary", "")
        llm_calls = state_values.get("llm_calls", 4)

        turns = []
        for i, msg in enumerate(messages):
            msg_type = getattr(msg, "type", "")
            text_content = _extract_text(getattr(msg, "content", ""))

            if msg_type in ("human", "user"):
                turns.append({
                    "id": f"turn_user_{i}",
                    "role": "user",
                    "userContent": text_content,
                    "timestamp": "Saved Journey",
                })
            elif msg_type in ("ai", "assistant"):
                turns.append({
                    "id": f"turn_assistant_{i}",
                    "role": "assistant",
                    "planResult": text_content,
                    "flightData": flight_results if i == len(messages) - 1 else None,
                    "hotelData": hotel_results if i == len(messages) - 1 else None,
                    "weatherData": weather_results if i == len(messages) - 1 else None,
                    "mapsData": maps_results if i == len(messages) - 1 else None,
                    "itineraryData": itinerary if i == len(messages) - 1 else None,
                    "llmCalls": llm_calls,
                    "timestamp": "Saved Journey",
                    "isStreaming": False,
                })

        return {"turns": turns, "thread_id": thread_id}
    except Exception as e:
        logger.warning(f"Could not load thread history for {pseudonymize_id(thread_id)}: {e}")
        return {"turns": [], "thread_id": thread_id}

@app.delete("/api/session/{thread_id}")
async def delete_session(
    thread_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Safely deletes thread ownership and all LangGraph checkpoints for the authenticated user.
    """
    success = safe_delete_user_thread(user.id, thread_id)
    if success:
        logger.info(f"Successfully deleted checkpoints and thread: {pseudonymize_id(thread_id)} | User: {pseudonymize_id(user.id)}")
        return {"status": "deleted", "thread_id": thread_id}
    else:
        raise HTTPException(status_code=404, detail="Thread not found")

@app.get("/api/threads")
async def list_threads(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Returns all travel threads owned by the authenticated user.
    """
    threads = get_user_threads(user.id)
    return {"threads": [t.model_dump() for t in threads]}

# Real-time Server-Sent Events (SSE) Streaming Endpoint
@app.post("/api/plan/stream")
async def plan_stream(
    payload: TravelRequest,
    user: AuthenticatedUser = Depends(check_rate_limit_for("plan")),
):
    user_query = payload.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if payload.thread_id:
        if not verify_thread_ownership(user.id, payload.thread_id):
            raise HTTPException(status_code=404, detail="Thread not found")
        thread_id = payload.thread_id
    else:
        thread_id = create_user_thread(user.id, title=user_query[:50])

    user_id = user.user_id_str
    logger.info(f"Incoming Streaming Travel Request | Thread: {pseudonymize_id(thread_id)} | User: {pseudonymize_id(user_id)} | QueryLength: {len(user_query)}")

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id,
        },
        "run_name": f"TourAI Plan: {user_query[:35]}",
        "tags": ["tourai-swarm", "langgraph-agent"],
        "metadata": {
            "thread_id": thread_id,
            "user_query": user_query,
        },
    }

    # Check if this thread has prior state in the Postgres checkpointer
    checkpoint_state = travel_graph.get_state(config)
    is_existing_session = bool(checkpoint_state and checkpoint_state.values)

    if is_existing_session:
        # Existing session: pass only the new user message so prior memory is preserved
        initial_state = {
            "messages": [HumanMessage(content=user_query)],
            "user_query": user_query,
        }
    else:
        # Brand new session: initialize empty defaults
        initial_state = {
            "messages": [HumanMessage(content=user_query)],
            "user_query": user_query,
            "destination": "",
            "flight_results": "",
            "hotel_results": "",
            "weather_results": "",
            "maps_results": "",
            "itinerary": "",
            "llm_calls": 0,
        }

    async def event_generator():
        if is_existing_session and checkpoint_state:
            accumulated_state = dict(checkpoint_state.values)
            accumulated_state.update(initial_state)
        else:
            accumulated_state = dict(initial_state)

        try:
            # Stream updates from the LangGraph execution graph
            for update in travel_graph.stream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_output in update.items():
                    # Catch LangGraph HITL interrupt event immediately
                    if node_name == "__interrupt__":
                        interrupt_items = node_output if isinstance(node_output, (list, tuple)) else [node_output]
                        first_interrupt = interrupt_items[0] if interrupt_items else None
                        logger.info(f"Workflow paused at HITL interrupt | Thread: {pseudonymize_id(thread_id)}")
                        approval_payload = _build_approval_payload(thread_id, first_interrupt, accumulated_state)
                        yield f"data: {json.dumps(approval_payload)}\n\n"
                        return

                    if isinstance(node_output, dict):
                        accumulated_state.update(node_output)

                    # Trigger UI fan_out indicator only when specialist tool agents are actually scheduled
                    if node_name == "supervisor" and accumulated_state.get("intent") != "follow_up":
                        yield f"data: {json.dumps({'event': 'fan_out_start', 'message': 'Dispatched specialist MCP agents'})}\n\n"
                        await asyncio.sleep(0.01)

                    # Handle immediate early exit if blocked by input guardrail
                    if node_name == "guardrail_blocked":
                        block_msg = accumulated_state.get("guardrail_reason") or "I can only help with travel-planning requests (destinations, flights, hotels, weather, budgets, and itineraries)."
                        sanitized_reason, _ = sanitize_text(block_msg)
                        async for chunk in _stream_token_chunks(sanitized_reason):
                            yield chunk
                        yield f"data: {json.dumps({'event': 'complete', 'thread_id': thread_id, 'answer': sanitized_reason, 'llm_calls': accumulated_state.get('llm_calls', 0)})}\n\n"
                        return

                    # Extract safe node progress payload (minimal metadata, no raw tool results)
                    node_payload = {
                        "event": "node_complete",
                        "node": node_name,
                        "intent": accumulated_state.get("intent", ""),
                        "llm_calls": accumulated_state.get("llm_calls", 0),
                    }

                    if node_name == "output_guardrail":
                        messages = node_output.get("messages", [])
                        if messages:
                            final_text = _extract_text(messages[-1].content)
                            yield f"data: {json.dumps({'event': 'node_complete', 'node': 'final_agent', 'llm_calls': accumulated_state.get('llm_calls', 0)})}\n\n"
                            async for chunk in _stream_token_chunks(final_text):
                                yield chunk
                    else:
                        yield f"data: {json.dumps(node_payload)}\n\n"
                        await asyncio.sleep(0.02)

            # Check if execution paused on Human-in-the-Loop (HITL) interrupt
            post_stream_state = travel_graph.get_state(config)
            if post_stream_state.tasks and any(t.interrupts for t in post_stream_state.tasks):
                interrupt_item = post_stream_state.tasks[0].interrupts[0]
                logger.info(f"Workflow paused for Human-in-the-Loop approval | Thread: {pseudonymize_id(thread_id)}")
                approval_payload = _build_approval_payload(thread_id, interrupt_item, accumulated_state)
                yield f"data: {json.dumps(approval_payload)}\n\n"
                return

            # Final complete event
            messages = accumulated_state.get("messages", [])
            final_answer = _extract_text(messages[-1].content) if messages else ""

            complete_payload = {
                "event": "complete",
                "thread_id": thread_id,
                "answer": final_answer,
                "llm_calls": accumulated_state.get("llm_calls", 0),
            }
            yield f"data: {json.dumps(complete_payload)}\n\n"

        except asyncio.CancelledError:
            logger.info(f"SSE client disconnected | Thread: {pseudonymize_id(thread_id)} | Stream closed normally by client.")
            raise
        except Exception as e:
            logger.error(f"Error in streaming Multi-Agent workflow: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': 'An unexpected error occurred during execution. Please try again.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


# Real-time Streaming Resume Endpoint (SSE)
@app.post("/api/plan/resume/stream")
async def resume_stream(
    payload: ResumeRequest,
    user: AuthenticatedUser = Depends(check_rate_limit_for("resume")),
):
    thread_id = payload.thread_id.strip() if payload.thread_id else ""
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required.")

    if not verify_thread_ownership(user.id, thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")

    feedback = payload.feedback.strip() if payload.feedback else ""
    if len(feedback) > 1500:
        raise HTTPException(status_code=400, detail="Feedback exceeds maximum length of 1500 characters.")

    # Validate feedback through input guardrail before resuming streaming workflow
    if feedback:
        allowed, reason = check_input_safety(feedback, is_feedback=True)
        if not allowed:
            logger.warning(f"Streaming resume feedback blocked by guardrail | Thread: {pseudonymize_id(thread_id)} | Reason: {reason}")
            raise HTTPException(status_code=400, detail=f"Feedback rejected by safety guardrail: {reason}")

    user_id = user.user_id_str
    logger.info(f"Incoming Streaming Resume | Thread: {pseudonymize_id(thread_id)} | User: {pseudonymize_id(user_id)} | Approved: {payload.approved} | FeedbackLength: {len(feedback)}")

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id,
        },
        "run_name": f"TourAI Resume: {thread_id[:12]}",
        "tags": ["tourai-hitl-resume"],
    }

    async def event_generator():
        try:
            resume_command = Command(
                resume={
                    "approved": payload.approved,
                    "feedback": feedback,
                }
            )

            accumulated_state = {}
            prior_state = travel_graph.get_state(config)
            if prior_state and prior_state.values:
                accumulated_state = dict(prior_state.values)

            for update in travel_graph.stream(resume_command, config=config, stream_mode="updates"):
                for node_name, node_output in update.items():
                    if isinstance(node_output, dict):
                        accumulated_state.update(node_output)

                    if node_name == "output_guardrail":
                        messages = node_output.get("messages", [])
                        if messages:
                            final_text = _extract_text(messages[-1].content)
                            yield f"data: {json.dumps({'event': 'node_complete', 'node': 'final_agent', 'llm_calls': accumulated_state.get('llm_calls', 0)})}\n\n"
                            async for chunk in _stream_token_chunks(final_text):
                                yield chunk
                    else:
                        node_payload = {
                            "event": "node_complete",
                            "node": node_name,
                            "llm_calls": accumulated_state.get("llm_calls", 0),
                        }
                        yield f"data: {json.dumps(node_payload)}\n\n"
                        await asyncio.sleep(0.02)

            # Final complete event
            messages = accumulated_state.get("messages", [])
            final_raw = accumulated_state.get("final_response") or (messages[-1].content if messages else "")
            final_answer = _extract_text(final_raw)

            complete_payload = {
                "event": "complete",
                "thread_id": thread_id,
                "answer": final_answer,
                "llm_calls": accumulated_state.get("llm_calls", 0),
            }
            yield f"data: {json.dumps(complete_payload)}\n\n"

        except asyncio.CancelledError:
            logger.info(f"SSE client disconnected | Thread: {pseudonymize_id(thread_id)} | Stream closed normally by client.")
            raise
        except Exception as e:
            logger.error(f"Error in streaming resume workflow: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': 'An unexpected error occurred during resumption. Please try again.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )



# Direct Runner (python app.py)
if __name__ == "__main__":
    logger.info("Starting FastAPI server at http://127.0.0.1:8000")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)