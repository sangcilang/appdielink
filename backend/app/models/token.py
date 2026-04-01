"""
Token ORM Model
"""
from datetime import datetime
import uuid
from sqlalchemy import Boolean, Column, DateTime, String, Uuid
from app.core.database import Base

class Token(Base):
    """Refresh token table"""
    __tablename__ = "tokens"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    refresh_token = Column(String(512), nullable=False, unique=True)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<Token(id={self.id}, user_id={self.user_id})>"
