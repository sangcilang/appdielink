"""
Access control schemas.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ShareDocumentRequest(BaseModel):
    """Body payload for document sharing requests."""
    user_ids: list[UUID] = Field(default_factory=list)


class CreateShareLinkRequest(BaseModel):
    """Request payload for a temporary multi-file share link."""
    document_ids: list[UUID] = Field(..., min_length=1)


class ShareLinkResponse(BaseModel):
    """Response payload for a temporary share link."""
    share_url: str
    expires_at: datetime
    expires_in_seconds: int
