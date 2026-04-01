"""
Document Management Endpoints
"""
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentRegisterBlob, DocumentResponse, DocumentUpdate
from app.repositories.document_repo import DocumentRepository
from app.services.file_service import FileService

router = APIRouter()

@router.post("/register-blob", response_model=DocumentResponse)
async def register_blob_document(
    payload: DocumentRegisterBlob,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_service = FileService()
    filename = Path(payload.filename).name

    if not (payload.blob_url.startswith("https://") or payload.blob_url.startswith("http://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid blob_url",
        )

    is_valid, message = file_service.validate_file(filename, payload.file_size)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    doc_repo = DocumentRepository(db)
    document = DocumentCreate(
        title=Path(filename).stem,
        description=None,
        is_public=False,
    )
    db_document = doc_repo.create(
        document=document,
        owner_id=current_user.id,
        file_path=payload.blob_url,
        file_size=payload.file_size,
        file_type=Path(filename).suffix.lstrip(".").lower(),
    )
    return db_document

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a new document
    """
    file_service = FileService()
    original_filename = Path(file.filename or "").name

    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file
    is_valid, message = file_service.validate_file(original_filename, len(content))
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Save file (local or Blob)
    file_path = await file_service.save_file(current_user.id, original_filename, content)
    
    # Create document record
    doc_repo = DocumentRepository(db)
    document = DocumentCreate(
        title=Path(original_filename).stem,
        description=None,
        is_public=False
    )
    
    db_document = doc_repo.create(
        document=document,
        owner_id=current_user.id,
        file_path=file_path,
        file_size=len(content),
        file_type=Path(original_filename).suffix.lstrip(".").lower()
    )
    
    return db_document

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get document details by ID
    """
    doc_repo = DocumentRepository(db)
    document = doc_repo.get_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this document"
        )

    return document

@router.get("/", response_model=list[DocumentResponse])
async def list_user_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all documents for current user
    """
    doc_repo = DocumentRepository(db)
    documents = doc_repo.get_user_documents(current_user.id, skip, limit)
    
    return documents

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    document: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update document details
    """
    doc_repo = DocumentRepository(db)
    existing_doc = doc_repo.get_by_id(document_id)

    if not existing_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if existing_doc.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this document"
        )

    updated_doc = doc_repo.update(document_id, document)
    return updated_doc

@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a document
    """
    doc_repo = DocumentRepository(db)
    existing_doc = doc_repo.get_by_id(document_id)

    if not existing_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if existing_doc.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this document"
        )

    await FileService().delete_file(existing_doc.file_path)
    success = doc_repo.delete(document_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {"message": "Document deleted successfully"}
