import os
import time
import uuid
import jwt
from jwt import PyJWKSet
import httpx
from typing import Optional, Dict, Any
from Multi_Agent_TourAI.auth.models import AuthenticatedUser
from Multi_Agent_TourAI.utils import get_logger

logger = get_logger("Multi_Agent_TourAI.auth.jwt")

# Strict algorithm allowlist - never trust the token's requested algorithm blindly
STRICT_ALLOWED_ALGORITHMS = ["RS256", "ES256", "HS256"]


class AuthVerificationError(Exception):
    """Base exception for authentication verification failures (HTTP 401)."""
    pass


class AuthVerificationServiceUnavailable(Exception):
    """Raised when authentication service / JWKS endpoint is unreachable (HTTP 503)."""
    pass


class SupabaseJWTValidator:
    """
    Centralized Supabase JWT Validator.
    Verifies cryptographic signatures, issuer, audience, expiration, algorithm,
    and user UUID subject.
    Supports:
      1. Asymmetric JWKS (RS256, ES256) with in-memory public key caching.
      2. Symmetric HS256 using SUPABASE_JWT_SECRET.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        jwt_secret: Optional[str] = None,
        jwks_cache_ttl: int = 3600,
    ):
        self.supabase_url = (
            supabase_url or os.getenv("SUPABASE_URL", "")
        ).rstrip("/")
        self.jwt_secret = jwt_secret or os.getenv("SUPABASE_JWT_SECRET", "")
        self.jwks_cache_ttl = jwks_cache_ttl
        self._jwks_cache: Dict[str, Any] = {}
        self._jwks_last_fetched: float = 0.0

    @property
    def expected_issuer(self) -> Optional[str]:
        if self.supabase_url:
            return f"{self.supabase_url}/auth/v1"
        return None

    def _get_jwks(self) -> Dict[str, Any]:
        """Fetches and caches JWKS from Supabase Auth endpoint."""
        now = time.time()
        if self._jwks_cache and (now - self._jwks_last_fetched < self.jwks_cache_ttl):
            return self._jwks_cache

        if not self.supabase_url:
            raise AuthVerificationServiceUnavailable(
                "SUPABASE_URL is not configured; cannot fetch JWKS."
            )

        jwks_url = f"{self.supabase_url}/auth/v1/.well-known/jwks.json"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(jwks_url)
                if resp.status_code != 200:
                    raise AuthVerificationServiceUnavailable(
                        f"Failed to fetch JWKS from Supabase: status {resp.status_code}"
                    )
                jwks_data = resp.json()
                jwk_set = PyJWKSet.from_dict(jwks_data)
                cache = {jwk.key_id: jwk.key for jwk in jwk_set.keys if jwk.key_id}
                self._jwks_cache = cache
                self._jwks_last_fetched = now
                logger.info(f"Refreshed Supabase JWKS cache with {len(cache)} keys (ES256/RS256).")
                return self._jwks_cache
        except httpx.RequestError as e:
            if self._jwks_cache:
                logger.warning(f"JWKS fetch failed, using expired cache: {e}")
                return self._jwks_cache
            raise AuthVerificationServiceUnavailable(
                f"Authentication service unavailable (JWKS unreachable): {e}"
            ) from e

    def verify_token(self, token: str) -> AuthenticatedUser:
        """
        Verifies a Supabase access token.
        Returns an AuthenticatedUser if valid.
        Raises AuthVerificationError (401) or AuthVerificationServiceUnavailable (503).
        """
        if not token or not isinstance(token, str):
            raise AuthVerificationError("Missing or malformed token.")

        # 1. Inspect unverified header for algorithm & key ID
        try:
            header = jwt.get_unverified_header(token)
        except Exception as e:
            logger.warning(f"[AUTH] Could not decode JWT header: {e}")
            raise AuthVerificationError("Invalid JWT header.") from e

        alg = header.get("alg")
        if not alg or alg not in STRICT_ALLOWED_ALGORITHMS:
            logger.warning(f"[AUTH] Rejected disallowed algorithm: {alg}")
            raise AuthVerificationError(f"Unsupported or disallowed algorithm: {alg}")

        # 2. Signature verification based on algorithm
        payload: Dict[str, Any] = {}
        decode_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": True,
            "verify_iss": bool(self.expected_issuer),
        }

        try:
            if alg in ["RS256", "ES256"]:
                kid = header.get("kid")
                jwks = self._get_jwks()
                if not kid or kid not in jwks:
                    raise AuthVerificationError(f"Unknown or missing key ID (kid: {kid}).")
                public_key = jwks[kid]

                payload = jwt.decode(
                    token,
                    public_key,
                    algorithms=[alg],
                    audience="authenticated",
                    issuer=self.expected_issuer,
                    options=decode_options,
                )

            elif alg == "HS256":
                if not self.jwt_secret:
                    logger.error("[AUTH] HS256 token received but SUPABASE_JWT_SECRET is not configured.")
                    raise AuthVerificationServiceUnavailable(
                        "Server authentication configuration error: JWT secret missing."
                    )

                payload = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=["HS256"],
                    audience="authenticated",
                    issuer=self.expected_issuer,
                    options=decode_options,
                )

        except jwt.ExpiredSignatureError as e:
            logger.info("[AUTH] Token expired.")
            raise AuthVerificationError("Token has expired.") from e
        except jwt.InvalidAudienceError as e:
            logger.warning("[AUTH] Invalid audience in token.")
            raise AuthVerificationError("Invalid token audience.") from e
        except jwt.InvalidIssuerError as e:
            logger.warning("[AUTH] Invalid issuer in token.")
            raise AuthVerificationError("Invalid token issuer.") from e
        except jwt.InvalidSignatureError as e:
            logger.warning("[AUTH] Cryptographic signature verification failed.")
            raise AuthVerificationError("Invalid token signature.") from e
        except jwt.PyJWTError as e:
            logger.warning(f"[AUTH] JWT validation failure: {e}")
            raise AuthVerificationError(f"Token validation failed: {str(e)}") from e

        # 3. Subject verification (valid UUID)
        sub = payload.get("sub")
        if not sub:
            raise AuthVerificationError("Token subject (sub) is missing.")

        try:
            user_uuid = uuid.UUID(str(sub))
        except (ValueError, TypeError) as e:
            logger.warning(f"[AUTH] Token subject is not a valid UUID: {sub}")
            raise AuthVerificationError("Token subject is not a valid user UUID.") from e

        return AuthenticatedUser(
            id=user_uuid,
            email=payload.get("email", ""),
            role=payload.get("role", "authenticated"),
            app_metadata=payload.get("app_metadata", {}),
            user_metadata=payload.get("user_metadata", {}),
        )


# Global singleton instance
_jwt_validator: Optional[SupabaseJWTValidator] = None


def get_jwt_validator() -> SupabaseJWTValidator:
    global _jwt_validator
    if _jwt_validator is None:
        _jwt_validator = SupabaseJWTValidator()
    return _jwt_validator

