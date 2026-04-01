"""
Document Pydantic Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID

class DocumentBase(BaseModel):
    """Base schema for document"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False

class DocumentCreate(DocumentBase):
    """Schema for creating document"""
    pass

class DocumentRegisterBlob(BaseModel):
    """Schema for registering an uploaded Blob as a Document record."""
    filename: str = Field(..., min_length=1, max_length=255)
    blob_url: str = Field(..., min_length=8, max_length=2048)
    file_size: int = Field(..., ge=1)
    content_type: Optional[str] = None

class DocumentUpdate(BaseModel):
    """Schema for updating document"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None

class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: UUID
    file_size: int
    file_type: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
