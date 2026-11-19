import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class AppUserPublic(BaseModel):
    """
    Safe public user representation returned in API responses.
    """
    id: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool = False
    created_at: Optional[datetime] = None


class AuthenticatedUser(BaseModel):
    """
    Represents an authenticated user context derived from a cryptographically
    verified application JWT.
    """
    id: uuid.UUID
    email: str
    display_name: Optional[str] = None
    session_id: Optional[uuid.UUID] = None
    role: str = "authenticated"

    @property
    def user_id_str(self) -> str:
        return str(self.id)


class RegisterRequest(BaseModel):
    """
    User registration payload.
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    """
    Email/password login payload.
    """
    email: EmailStr
    password: str = Field(..., max_length=128)


class RequestPasswordSetupRequest(BaseModel):
    """
    Request an onboarding verification link or password setup token.
    """
    email: EmailStr


class CompletePasswordSetupRequest(BaseModel):
    """
    Complete password setup using a verified single-use time-limited token.
    """
    token: str = Field(..., min_length=16, max_length=256)
    new_password: str = Field(..., min_length=8, max_length=128)


class AuthResponse(BaseModel):
    """
    Successful authentication response with short-lived access token and user info.
    (Refresh token is delivered strictly via HttpOnly cookie).
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # seconds (15 minutes)
    user: AppUserPublic


class ThreadSummary(BaseModel):
    """
    Summary of a travel journey thread owned by an authenticated user.
    """
    thread_id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
