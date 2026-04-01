"""
Document Repository - Database access layer
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate

class DocumentRepository:
    """Repository for document database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, document: DocumentCreate, owner_id: UUID, file_path: str, file_size: int, file_type: str) -> Document:
        """Create a new document"""
        db_document = Document(
            title=document.title,
            description=document.description,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            owner_id=owner_id,
            is_public=document.is_public
        )
        self.db.add(db_document)
        self.db.commit()
        self.db.refresh(db_document)
        return db_document
    
    def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID"""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_user_documents(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get all documents for a user"""
        return self.db.query(Document).filter(Document.owner_id == user_id).offset(skip).limit(limit).all()
    
    def get_public_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get all public documents"""
        return self.db.query(Document).filter(Document.is_public == True).offset(skip).limit(limit).all()
    
    def update(self, document_id: UUID, document: DocumentUpdate) -> Optional[Document]:
        """Update a document"""
        db_document = self.get_by_id(document_id)
        if db_document:
            if document.title:
                db_document.title = document.title
            if document.description is not None:
                db_document.description = document.description
            if document.is_public is not None:
                db_document.is_public = document.is_public
            self.db.commit()
            self.db.refresh(db_document)
        return db_document
    
    def delete(self, document_id: UUID) -> bool:
        """Delete a document"""
        db_document = self.get_by_id(document_id)
        if db_document:
            self.db.delete(db_document)
            self.db.commit()
            return True
        return False
