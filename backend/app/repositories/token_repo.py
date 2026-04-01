"""
Token Repository - Database access layer for tokens
"""
from typing import Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.token import Token

class TokenRepository:
    """Repository for token database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_id: UUID, refresh_token: str, expires_at: datetime) -> Token:
        """Create a refresh token record"""
        db_token = Token(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        self.db.add(db_token)
        self.db.commit()
        self.db.refresh(db_token)
        return db_token
    
    def get_by_token(self, refresh_token: str) -> Optional[Token]:
        """Get token record by refresh token"""
        return self.db.query(Token).filter(Token.refresh_token == refresh_token).first()
    
    def get_by_user_id(self, user_id: UUID) -> list[Token]:
        """Get all tokens for a user"""
        return self.db.query(Token).filter(Token.user_id == user_id).all()
    
    def revoke_token(self, user_id: UUID, refresh_token: str) -> bool:
        """Revoke a refresh token"""
        token = self.get_by_token(refresh_token)
        if token and token.user_id == user_id:
            token.is_revoked = True
            self.db.commit()
            return True
        return False
    
    def revoke_all_user_tokens(self, user_id: UUID) -> bool:
        """Revoke all tokens for a user"""
        self.db.query(Token).filter(Token.user_id == user_id).update({"is_revoked": True})
        self.db.commit()
        return True
    
    def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens from database"""
        result = self.db.query(Token).filter(Token.expires_at < datetime.utcnow()).delete()
        self.db.commit()
        return result
