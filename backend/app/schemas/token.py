"""
Token Pydantic Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

class TokenBase(BaseModel):
    """Base schema for token"""
    access_token: str
    token_type: str = "bearer"

class TokenResponse(TokenBase):
    """Schema for token response"""
    refresh_token: Optional[str] = None

class TokenPayload(BaseModel):
    """Schema for JWT payload"""
    user_id: UUID
    exp: datetime
    iat: datetime

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str
