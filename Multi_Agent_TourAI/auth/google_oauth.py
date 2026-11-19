import os
import time
import base64
import hashlib
import secrets
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv
import requests
import jwt
from jwt import PyJWKClient
from Multi_Agent_TourAI.auth.models import AuthenticatedUser
from Multi_Agent_TourAI.auth.auth_repository import (
    get_identity_by_provider,
    get_user_by_email,
    get_user_by_id,
    create_google_user,
    link_verified_google_identity,
)
from Multi_Agent_TourAI.utils import get_logger

load_dotenv()

logger = get_logger("Multi_Agent_TourAI.auth.google_oauth")

def _get_client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()

def _get_client_secret() -> str:
    return os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

def _get_redirect_uri() -> str:
    return os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback").strip()

def _get_frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:3000").strip()

GOOGLE_CLIENT_ID = _get_client_id()
GOOGLE_CLIENT_SECRET = _get_client_secret()
GOOGLE_REDIRECT_URI = _get_redirect_uri()
FRONTEND_URL = _get_frontend_url()

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"

# In-memory temporary state store (state -> {code_verifier, nonce, created_at})
_oauth_states: Dict[str, Dict[str, Any]] = {}
_STATE_TTL_SECONDS = 600  # 10 minutes
_jwk_client: Optional[PyJWKClient] = None


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(GOOGLE_JWKS_URL, cache_keys=True, max_cached_keys=10)
    return _jwk_client


def _generate_pkce_pair() -> Tuple[str, str]:
    """Generates a high-entropy PKCE code_verifier and code_challenge (S256)."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def _prune_expired_states() -> None:
    """Removes states older than _STATE_TTL_SECONDS."""
    now = time.time()
    expired = [k for k, v in _oauth_states.items() if now - v.get("created_at", 0) > _STATE_TTL_SECONDS]
    for k in expired:
        _oauth_states.pop(k, None)


def generate_google_auth_url(redirect_uri: Optional[str] = None) -> Tuple[str, str]:
    """
    Constructs the Google OAuth 2.0 authorization URL with PKCE (S256), state, and nonce.
    Returns (auth_url, state).
    """
    _prune_expired_states()
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    code_verifier, code_challenge = _generate_pkce_pair()

    _oauth_states[state] = {
        "code_verifier": code_verifier,
        "nonce": nonce,
        "created_at": time.time(),
        "redirect_uri": redirect_uri or GOOGLE_REDIRECT_URI,
    }

    client_id = _get_client_id()
    effective_redirect_uri = redirect_uri or _get_redirect_uri()

    params = {
        "client_id": client_id,
        "redirect_uri": effective_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "select_account",
    }
    encoded = requests.compat.urlencode(params)  # type: ignore
    auth_url = f"{GOOGLE_AUTH_ENDPOINT}?{encoded}"
    return auth_url, state


def verify_google_id_token(id_token_str: str, expected_nonce: Optional[str] = None) -> Dict[str, Any]:
    """
    Cryptographically verifies a Google ID token using Google's public JWKS.
    Enforces audience, issuer (accounts.google.com), expiration, and nonce.
    """
    jwk_client = _get_jwk_client()
    client_id = _get_client_id()
    try:
        signing_key = jwk_client.get_signing_key_from_jwt(id_token_str)
        claims = jwt.decode(
            id_token_str,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id if client_id else None,
            options={"verify_aud": bool(client_id), "verify_exp": True},
        )
    except Exception as e:
        logger.error(f"[AUTH] Google ID token verification failed: {e}")
        raise ValueError("Invalid Google ID token signature or claims.")

    issuer = claims.get("iss", "")
    if issuer not in ("https://accounts.google.com", "accounts.google.com"):
        raise ValueError(f"Invalid Google token issuer: {issuer}")

    if expected_nonce and claims.get("nonce") != expected_nonce:
        raise ValueError("Google ID token nonce mismatch.")

    if not claims.get("email_verified", False):
        raise ValueError("Google account email is not verified.")

    sub = claims.get("sub")
    if not sub:
        raise ValueError("Google ID token missing subject ('sub') claim.")

    return claims


def process_google_callback(code: str, state: str) -> Dict[str, Any]:
    """
    Exchanges code for tokens, verifies Google ID token, matches or creates user identity,
    and prevents insecure automatic account linking.
    """
    _prune_expired_states()
    state_data = _oauth_states.pop(state, None)
    if not state_data:
        raise ValueError("Invalid or expired OAuth state parameter.")

    code_verifier = state_data["code_verifier"]
    expected_nonce = state_data["nonce"]
    redirect_uri = state_data.get("redirect_uri", GOOGLE_REDIRECT_URI)

    # 1. Exchange authorization code for tokens
    payload = {
        "code": code,
        "client_id": _get_client_id(),
        "client_secret": _get_client_secret(),
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
    }

    try:
        token_res = requests.post(GOOGLE_TOKEN_ENDPOINT, data=payload, timeout=10)
    except Exception as e:
        logger.error(f"[AUTH] Error contacting Google token endpoint: {e}")
        raise ValueError("Failed to connect to Google OAuth service.")

    if not token_res.ok:
        logger.error(f"[AUTH] Google token exchange error: {token_res.text}")
        raise ValueError("Google token exchange failed.")

    token_json = token_res.json()
    id_token_str = token_json.get("id_token")
    if not id_token_str:
        raise ValueError("Google token response did not contain id_token.")

    # 2. Cryptographically verify ID token
    claims = verify_google_id_token(id_token_str, expected_nonce=expected_nonce)
    google_sub = str(claims["sub"])
    email = str(claims.get("email", "")).strip().lower()
    email_verified = claims.get("email_verified") is True
    display_name = claims.get("name") or email.split("@")[0]
    avatar_url = claims.get("picture")

    # 3. Match Google Identity
    existing_identity = get_identity_by_provider("google", google_sub)
    if existing_identity:
        user = get_user_by_id(existing_identity["user_id"])
        if not user:
            raise ValueError("User account associated with this Google identity was deactivated.")
        return user

    # 4. Check if an account already exists with this email
    existing_user = get_user_by_email(email)
    if existing_user:
        # Secure Account Linking:
        # Require that Google cryptographically verified this email
        if not email_verified:
            logger.warning(
                f"[SECURITY] Refusing Google link for existing account {existing_user['id']} ({email}): "
                "Google email is not verified."
            )
            raise ValueError("Google account email is not verified by Google.")

        logger.info(
            f"[AUTH] Safely linking verified Google identity (sub={google_sub}) "
            f"to existing account {existing_user['id']} ({email})"
        )
        linked_user = link_verified_google_identity(
            user_id=existing_user["id"],
            google_sub=google_sub,
            avatar_url=avatar_url,
        )
        return linked_user

    # 5. Create new user with Google identity
    if not email_verified:
        raise ValueError("Google account email must be verified to sign up.")

    new_user = create_google_user(
        email=email,
        google_sub=google_sub,
        display_name=display_name,
        avatar_url=avatar_url,
    )
    return new_user

