"""
Document ORM Model
"""
from datetime import datetime
import uuid
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Uuid
from app.core.database import Base

class Document(Base):
    """Document table"""
    __tablename__ = "documents"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    owner_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title})>"
