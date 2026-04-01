"""
ShareLink Repository - Database access layer for share links
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.share_link import ShareLink


class ShareLinkRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        jti: str,
        creator_id: UUID | None,
        document_ids_json: str,
        expires_at: datetime,
    ) -> ShareLink:
        record = ShareLink(
            jti=jti,
            creator_id=creator_id,
            document_ids_json=document_ids_json,
            expires_at=expires_at,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_jti(self, jti: str) -> Optional[ShareLink]:
        return self.db.query(ShareLink).filter(ShareLink.jti == jti).first()

    def mark_used(self, jti: str) -> bool:
        record = self.get_by_jti(jti)
        if not record:
            return False
        if record.used_at is not None:
            return True
        record.used_at = datetime.utcnow()
        self.db.commit()
        return True

