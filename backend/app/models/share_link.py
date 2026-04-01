"""
ShareLink ORM Model (one-time download links)
"""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, String, Text, Uuid

from app.core.database import Base


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti = Column(String(64), nullable=False, unique=True, index=True)
    creator_id = Column(Uuid(as_uuid=True), nullable=True, index=True)
    document_ids_json = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ShareLink(id={self.id}, jti={self.jti}, used_at={self.used_at})>"

