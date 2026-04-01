"""
Token Business Logic Service
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.repositories.token_repo import TokenRepository

class TokenService:
    """Service for token operations"""
    
    def __init__(self, token_repo: TokenRepository):
        self.token_repo = token_repo
    
    def create_tokens(self, user_id: UUID) -> dict:
        """Create access and refresh tokens"""
        access_token = create_access_token(
            data={"user_id": str(user_id), "type": "access"},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        refresh_expires_at = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        refresh_token = create_access_token(
            data={"user_id": str(user_id), "type": "refresh"},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        self.token_repo.revoke_all_user_tokens(user_id)
        self.token_repo.create(user_id, refresh_token, refresh_expires_at)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode token"""
        return decode_token(token)
    
    def revoke_token(self, user_id: UUID, token: str) -> bool:
        """Revoke a refresh token"""
        return self.token_repo.revoke_token(user_id, token)
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return hash_password(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return verify_password(plain_password, hashed_password)
