import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class AuthenticatedUser(BaseModel):
    """
    Represents an authenticated user whose identity has been verified
    cryptographically against Supabase JWT signatures.
    """
    id: uuid.UUID
    email: str = ""
    role: str = "authenticated"
    app_metadata: dict = Field(default_factory=dict)
    user_metadata: dict = Field(default_factory=dict)

    @property
    def user_id_str(self) -> str:
        return str(self.id)


class ThreadSummary(BaseModel):
    """
    Summary of a travel planning journey thread owned by a user.
    """
    thread_id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime

