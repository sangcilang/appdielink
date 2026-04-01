"""
Access Control and Permissions Endpoints
"""
import json
from datetime import datetime, timedelta
import mimetypes
from pathlib import Path
import tempfile
import zipfile
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from starlette.background import BackgroundTask
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.security import create_access_token, decode_token
from app.models.document import Document
from app.models.user import User
from app.repositories.document_repo import DocumentRepository
from app.repositories.share_link_repo import ShareLinkRepository
from app.services.file_service import FileService
from app.schemas.access import (
    CreateShareLinkRequest,
    ShareDocumentRequest,
    ShareLinkResponse,
)
from app.schemas.document import DocumentUpdate

router = APIRouter()


def _get_owned_documents(
    document_ids: list[UUID],
    current_user: User,
    db: Session,
) -> list[Document]:
    """Load and validate a deduplicated list of documents owned by the user."""
    doc_repo = DocumentRepository(db)
    documents: list[Document] = []
    seen_document_ids: set[UUID] = set()

    for document_id in document_ids:
        if document_id in seen_document_ids:
            continue

        document = doc_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )
        if document.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to share one or more selected documents",
            )

        documents.append(document)
        seen_document_ids.add(document_id)

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select at least one document to share",
        )

    return documents


def _build_share_link_response(
    request: Request,
    document_ids: list[UUID],
    current_user: User,
    db: Session,
) -> ShareLinkResponse:
    """Create a 5-minute signed share link for one or many documents."""
    expires_at = datetime.utcnow() + timedelta(
        minutes=settings.SHARE_LINK_EXPIRE_MINUTES
    )
    share_token = create_access_token(
        data={
            "document_ids": [str(document_id) for document_id in document_ids],
            "type": "share",
            "creator": {
                "username": current_user.username,
                "email": current_user.email,
            },
        },
        expires_delta=timedelta(minutes=settings.SHARE_LINK_EXPIRE_MINUTES),
    )
    payload = decode_token(share_token) or {}
    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate a share link",
        )

    exp_value = payload.get("exp")
    if isinstance(exp_value, (int, float)):
        expires_at = datetime.utcfromtimestamp(float(exp_value))

    ShareLinkRepository(db).create(
        jti=jti,
        creator_id=getattr(current_user, "id", None),
        document_ids_json=json.dumps([str(document_id) for document_id in document_ids]),
        expires_at=expires_at,
    )

    page_url = request.url_for("shared_link_page", share_token=share_token)
    if settings.PUBLIC_BASE_URL:
        share_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}{page_url.path}"
    else:
        share_url = str(page_url)

    return ShareLinkResponse(
        share_url=share_url,
        expires_at=expires_at,
        expires_in_seconds=settings.SHARE_LINK_EXPIRE_MINUTES * 60,
    )


def _build_download_name(document: Document) -> str:
    """Build the download name shown to the user."""
    if document.file_type:
        return f"{document.title}.{document.file_type}"
    return document.title


def _cleanup_temp_file(file_path: str) -> None:
    """Delete a temporary file after the response is sent."""
    Path(file_path).unlink(missing_ok=True)


def _mark_share_link_used(jti: str) -> None:
    db = SessionLocal()
    try:
        ShareLinkRepository(db).mark_used(jti)
    finally:
        db.close()


def _cleanup_and_mark_used(file_path: str, jti: str) -> None:
    try:
        _cleanup_temp_file(file_path)
    finally:
        _mark_share_link_used(jti)


def _is_remote_file_path(file_path: str) -> bool:
    return file_path.startswith("http://") or file_path.startswith("https://")


async def _stream_remote_file(url: str, *, filename: str, jti: str) -> StreamingResponse:
    from vercel.blob import AsyncBlobClient

    async with AsyncBlobClient() as client:
        result = await client.get(url, access=getattr(settings, "BLOB_ACCESS", "private"))
        if result is None or result.status_code != 200 or result.stream is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found",
            )

        headers = {
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
            "Expires": "0",
            "Content-Disposition": f'attachment; filename="{filename}"',
        }

        return StreamingResponse(
            result.stream,
            media_type=getattr(result, "content_type", None) or "application/octet-stream",
            headers=headers,
            background=BackgroundTask(_mark_share_link_used, jti),
        )


def _create_zip_archive(documents: list[Document]) -> tuple[str, str]:
    """Create a temporary ZIP archive containing the selected documents."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_file.close()
    used_names: dict[str, int] = {}

    with zipfile.ZipFile(temp_file.name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for document in documents:
            file_path = Path(document.file_path)
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document file not found for {document.id}",
                )

            base_name = _build_download_name(document)
            occurrence = used_names.get(base_name, 0)
            used_names[base_name] = occurrence + 1

            if occurrence:
                stem = Path(base_name).stem
                suffix = Path(base_name).suffix
                archive_name = f"{stem}-{occurrence + 1}{suffix}"
            else:
                archive_name = base_name

            archive.write(file_path, arcname=archive_name)

    zip_name = f"link1die-share-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip"
    return temp_file.name, zip_name

@router.post("/documents/{document_id}/share")
async def share_document(
    document_id: UUID,
    request: ShareDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Share a document with other users
    """
    document = DocumentRepository(db).get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to share this document"
        )

    return {
        "message": "Document sharing metadata accepted",
        "document_id": str(document_id),
        "shared_with": [str(user_id) for user_id in request.user_ids],
    }


@router.post(
    "/documents/{document_id}/share-link",
    response_model=ShareLinkResponse,
)
async def create_share_link(
    document_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a temporary share link that stays valid for 5 minutes.
    """
    documents = _get_owned_documents([document_id], current_user, db)
    return _build_share_link_response(
        request=request,
        document_ids=[document.id for document in documents],
        current_user=current_user,
        db=db,
    )


@router.post("/share-link", response_model=ShareLinkResponse)
async def create_multi_share_link(
    payload: CreateShareLinkRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a temporary share link for one or many selected documents.
    """
    documents = _get_owned_documents(payload.document_ids, current_user, db)
    return _build_share_link_response(
        request=request,
        document_ids=[document.id for document in documents],
        current_user=current_user,
        db=db,
    )

@router.post("/documents/{document_id}/make-public")
async def make_document_public(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Make a document publicly accessible
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
            detail="You do not have permission to update this document"
        )

    doc_repo.update(document_id, DocumentUpdate(is_public=True))
    return {
        "message": f"Document {document_id} is now public"
    }

@router.post("/documents/{document_id}/make-private")
async def make_document_private(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Make a document private
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
            detail="You do not have permission to update this document"
        )

    doc_repo.update(document_id, DocumentUpdate(is_public=False))
    return {
        "message": f"Document {document_id} is now private"
    }

@router.get("/documents/{document_id}/permissions")
async def get_document_permissions(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get access permissions for a document
    """
    document = DocumentRepository(db).get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view document permissions"
        )

    return {
        "document_id": str(document_id),
        "owner_id": str(document.owner_id),
        "is_public": document.is_public,
        "permissions": []
    }

def _public_base_url(request: Request) -> str:
    if settings.PUBLIC_BASE_URL:
        return settings.PUBLIC_BASE_URL.rstrip("/")
    return str(request.base_url).rstrip("/")


def _render_used_share_link_page(request: Request, payload: dict) -> HTMLResponse:
    creator = payload.get("creator") if isinstance(payload.get("creator"), dict) else {}
    username = creator.get("username") or "Người tạo link"
    email = creator.get("email")

    base_url = _public_base_url(request)
    email_line = (
        f'<a href="mailto:{email}">{email}</a>' if email else '<span class="muted">Chưa cập nhật</span>'
    )

    html = f"""<!doctype html>
<html lang="vi">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Link đã được sử dụng</title>
    <style>
      :root {{
        --bg: #0b1220;
        --card: rgba(255, 255, 255, 0.08);
        --border: rgba(255, 255, 255, 0.12);
        --text: rgba(255, 255, 255, 0.92);
        --muted: rgba(255, 255, 255, 0.65);
        --accent: #7c3aed;
        --shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background: radial-gradient(1000px 600px at 30% 10%, rgba(124, 58, 237, 0.22), transparent 55%), var(--bg);
        color: var(--text);
        font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial;
      }}
      .shell {{ width: min(720px, calc(100% - 32px)); padding: 28px; }}
      .card {{ border: 1px solid var(--border); background: var(--card); border-radius: 18px; box-shadow: var(--shadow); overflow: hidden; }}
      .header {{ padding: 24px; }}
      h1 {{ margin: 0 0 10px 0; font-size: 28px; letter-spacing: -0.02em; }}
      p {{ margin: 0; color: var(--muted); line-height: 1.6; }}
      .content {{ padding: 0 24px 24px 24px; display: grid; gap: 14px; }}
      .box {{ border: 1px solid rgba(255,255,255,0.12); border-radius: 14px; padding: 14px; background: rgba(0,0,0,0.16); }}
      .row {{ display: flex; justify-content: space-between; gap: 12px; padding: 10px 12px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.04); }}
      .muted {{ color: rgba(255,255,255,0.6); }}
      a {{ color: inherit; }}
      .btn {{ display:inline-flex; align-items:center; justify-content:center; padding: 12px 14px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.14); background: rgba(255,255,255,0.06); text-decoration:none; font-weight: 700; }}
      .btn.primary {{ border-color: rgba(124,58,237,0.55); background: rgba(124,58,237,0.25); }}
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="card" role="main">
        <div class="header">
          <h1>Link đã được sử dụng</h1>
          <p>Link tải xuống này chỉ dùng được 1 lần. Vui lòng liên hệ người tạo link để xin link mới.</p>
        </div>
        <div class="content">
          <div class="box">
            <div class="row"><span class="muted">Tài khoản</span><strong>{username}</strong></div>
            <div class="row"><span class="muted">Email</span><strong>{email_line}</strong></div>
          </div>
          <div>
            <a class="btn primary" href="{base_url}/">Về trang chủ</a>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>"""

    return HTMLResponse(
        content=html,
        status_code=status.HTTP_410_GONE,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
    )


def _render_share_link_landing_page(
    request: Request,
    payload: dict,
    documents: list[Document],
    download_url: str,
) -> HTMLResponse:
    creator = payload.get("creator") if isinstance(payload.get("creator"), dict) else {}
    username = creator.get("username") or "Người tạo link"
    expires_label = None
    exp_value = payload.get("exp")
    if isinstance(exp_value, (int, float)):
        expires_label = datetime.utcfromtimestamp(float(exp_value)).strftime("%Y-%m-%d %H:%M:%S UTC")

    file_lines = "\n".join(
        f"<li><strong>{_build_download_name(doc)}</strong> <span class='muted'>({doc.file_size} bytes)</span></li>"
        for doc in documents
    )

    html = f"""<!doctype html>
<html lang="vi">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tải xuống</title>
    <style>
      :root {{
        --bg: #0b1220;
        --card: rgba(255, 255, 255, 0.08);
        --border: rgba(255, 255, 255, 0.12);
        --text: rgba(255, 255, 255, 0.92);
        --muted: rgba(255, 255, 255, 0.65);
        --accent: #7c3aed;
        --shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background:
          radial-gradient(1200px 600px at 15% 10%, rgba(124, 58, 237, 0.22), transparent 55%),
          var(--bg);
        color: var(--text);
        font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial;
      }}
      .shell {{ width: min(780px, calc(100% - 32px)); padding: 28px; }}
      .card {{ border: 1px solid var(--border); background: var(--card); border-radius: 18px; box-shadow: var(--shadow); overflow: hidden; }}
      .header {{ padding: 24px 24px 10px 24px; }}
      h1 {{ margin: 0 0 8px 0; font-size: 28px; letter-spacing: -0.02em; }}
      p {{ margin: 0; color: var(--muted); line-height: 1.6; }}
      .content {{ padding: 18px 24px 24px 24px; display: grid; gap: 14px; }}
      .box {{ border: 1px solid rgba(255,255,255,0.12); border-radius: 14px; padding: 14px; background: rgba(0,0,0,0.16); }}
      ul {{ margin: 10px 0 0 18px; color: rgba(255,255,255,0.86); }}
      li {{ margin: 6px 0; }}
      .muted {{ color: rgba(255,255,255,0.6); }}
      a {{ color: inherit; }}
      .btn {{
        display:inline-flex;
        align-items:center;
        justify-content:center;
        padding: 14px 16px;
        border-radius: 14px;
        border: 1px solid rgba(124,58,237,0.55);
        background: rgba(124,58,237,0.28);
        text-decoration:none;
        font-weight: 800;
        width: 100%;
      }}
      .note {{ font-size: 13px; color: rgba(255,255,255,0.65); }}
      .grid {{ display: grid; gap: 10px; }}
      .row {{ display:flex; justify-content: space-between; gap: 12px; padding: 10px 12px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.04); }}
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="card" role="main">
        <div class="header">
          <h1>Tải xuống tệp</h1>
          <p>Người tạo link: <strong>{username}</strong></p>
        </div>
        <div class="content">
          <div class="box">
            <div class="grid">
              <div class="row"><span class="muted">Số lượng</span><strong>{len(documents)} tệp</strong></div>
              <div class="row"><span class="muted">Hết hạn</span><strong>{expires_label or '—'}</strong></div>
            </div>
            <ul>{file_lines}</ul>
          </div>
          <a class="btn" href="{download_url}">Bấm để tải xuống</a>
          <div class="note">Sau khi tải xuống, link sẽ hết hạn và không dùng lại được.</div>
        </div>
      </div>
    </div>
  </body>
</html>"""

    return HTMLResponse(
        content=html,
        status_code=status.HTTP_200_OK,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
    )


def _render_expired_share_link_page(request: Request, payload: dict) -> HTMLResponse:
    creator = payload.get("creator") if isinstance(payload.get("creator"), dict) else {}
    username = creator.get("username") or "Người tạo link"
    email = creator.get("email")
    phone = creator.get("phone") or creator.get("phone_number")

    email_row = (
        f"""
        <div class="row">
          <div class="label">Email</div>
          <div class="value"><a href="mailto:{email}">{email}</a></div>
        </div>
        """
        if email
        else """
        <div class="row">
          <div class="label">Email</div>
          <div class="value muted">Chưa cập nhật</div>
        </div>
        """
    )

    phone_row = (
        f"""
        <div class="row">
          <div class="label">SĐT</div>
          <div class="value"><a href="tel:{phone}">{phone}</a></div>
        </div>
        """
        if phone
        else """
        <div class="row">
          <div class="label">SĐT</div>
          <div class="value muted">Chưa cập nhật</div>
        </div>
        """
    )

    base_url = _public_base_url(request)
    html = f"""<!doctype html>
<html lang="vi">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Link đã hết hạn</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #0b1220;
        --card: rgba(255, 255, 255, 0.08);
        --border: rgba(255, 255, 255, 0.12);
        --text: rgba(255, 255, 255, 0.92);
        --muted: rgba(255, 255, 255, 0.65);
        --accent: #7c3aed;
        --accent-2: #06b6d4;
        --shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
      }}

      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background:
          radial-gradient(1200px 600px at 15% 10%, rgba(124, 58, 237, 0.22), transparent 55%),
          radial-gradient(1000px 500px at 85% 0%, rgba(6, 182, 212, 0.18), transparent 60%),
          radial-gradient(900px 500px at 70% 90%, rgba(124, 58, 237, 0.16), transparent 55%),
          var(--bg);
        color: var(--text);
        font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
      }}

      a {{ color: inherit; }}
      .shell {{ width: min(720px, calc(100% - 32px)); padding: 28px; }}
      .card {{
        border: 1px solid var(--border);
        background: var(--card);
        border-radius: 18px;
        box-shadow: var(--shadow);
        overflow: hidden;
      }}
      .header {{ padding: 24px 24px 10px 24px; }}
      .badge {{
        display: inline-flex;
        gap: 8px;
        align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 999px;
        padding: 8px 12px;
        color: rgba(255, 255, 255, 0.85);
        background: rgba(0, 0, 0, 0.18);
        font-size: 13px;
      }}
      .badge .dot {{
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.18);
      }}
      h1 {{
        margin: 14px 0 8px 0;
        font-size: 28px;
        letter-spacing: -0.02em;
      }}
      p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
      .content {{ padding: 18px 24px 24px 24px; display: grid; gap: 16px; }}
      .contact {{
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
        padding: 16px;
        background: rgba(0, 0, 0, 0.16);
      }}
      .contact-title {{ font-weight: 600; margin: 0 0 12px 0; }}
      .rows {{ display: grid; gap: 10px; }}
      .row {{
        display: grid;
        grid-template-columns: 110px 1fr;
        gap: 12px;
        align-items: center;
        padding: 10px 12px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.04);
      }}
      .label {{ color: rgba(255, 255, 255, 0.7); font-size: 13px; }}
      .value {{ font-weight: 600; word-break: break-word; }}
      .muted {{ font-weight: 500; color: rgba(255, 255, 255, 0.6); }}
      .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 6px; }}
      .btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 12px 14px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.14);
        background: rgba(255, 255, 255, 0.06);
        text-decoration: none;
        font-weight: 600;
      }}
      .btn.primary {{
        border-color: rgba(124, 58, 237, 0.55);
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.9), rgba(6, 182, 212, 0.45));
      }}
      .footer {{
        padding: 14px 24px 20px 24px;
        border-top: 1px solid rgba(255, 255, 255, 0.10);
        color: rgba(255, 255, 255, 0.58);
        font-size: 12px;
      }}
      .code {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        color: rgba(255, 255, 255, 0.75);
      }}
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="card" role="main">
        <div class="header">
          <div class="badge"><span class="dot"></span> Link1Die • Liên kết tạm thời</div>
          <h1>Link đã hết hạn</h1>
          <p>Liên kết tải xuống này đã hết hạn. Vui lòng liên hệ người tạo link để xin link mới.</p>
        </div>
        <div class="content">
          <div class="contact">
            <p class="contact-title">Thông tin liên hệ người tạo</p>
            <div class="rows">
              <div class="row">
                <div class="label">Tài khoản</div>
                <div class="value">{username}</div>
              </div>
              {phone_row}
              {email_row}
            </div>
            <div class="actions">
              <a class="btn primary" href="{base_url}/">Về trang chủ</a>
              <a class="btn" href="javascript:location.reload()">Thử lại</a>
            </div>
          </div>
        </div>
        <div class="footer">
          Nếu bạn vừa nhận link, có thể link chỉ có hiệu lực trong <span class="code">{settings.SHARE_LINK_EXPIRE_MINUTES} phút</span>.
        </div>
      </div>
    </div>
  </body>
</html>"""

    return HTMLResponse(
        content=html,
        status_code=status.HTTP_410_GONE,
        headers={
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/shared/{share_token}", name="shared_link_page")
async def shared_link_page(
    share_token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Landing page for a share link (shows a download button).
    """
    payload = decode_token(share_token)
    if not payload or payload.get("type") != "share":
        expired_payload = decode_token(share_token, verify_exp=False)
        if expired_payload and expired_payload.get("type") == "share":
            return _render_expired_share_link_page(request=request, payload=expired_payload)

        return HTMLResponse(
            content="Share link is invalid or has expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={
                "Cache-Control": "no-store",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        return HTMLResponse(
            content="Share link is invalid",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
        )

    share_record = ShareLinkRepository(db).get_by_jti(jti)
    if not share_record:
        return HTMLResponse(
            content="Share link is invalid or has expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
        )
    if share_record.used_at is not None:
        return _render_used_share_link_page(request=request, payload=payload)

    raw_document_ids = payload.get("document_ids")
    if raw_document_ids is None and payload.get("document_id") is not None:
        raw_document_ids = [payload.get("document_id")]

    if not raw_document_ids:
        return HTMLResponse(
            content="Share link is invalid or has expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
        )

    document_ids: list[UUID] = []
    for raw_document_id in raw_document_ids:
        try:
            document_ids.append(UUID(str(raw_document_id)))
        except ValueError as exc:
            return HTMLResponse(
                content="Share link is invalid or has expired",
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
            )

    documents = []
    doc_repo = DocumentRepository(db)
    for document_id in document_ids:
        document = doc_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )
        documents.append(document)

    download_route = request.url_for("download_shared_document_file", share_token=share_token)
    download_url = (
        f"{settings.PUBLIC_BASE_URL.rstrip('/')}{download_route.path}"
        if settings.PUBLIC_BASE_URL
        else str(download_route)
    )
    return _render_share_link_landing_page(
        request=request,
        payload=payload,
        documents=documents,
        download_url=download_url,
    )


@router.get("/shared/{share_token}/download", name="download_shared_document_file")
async def download_shared_document_file(
    share_token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Download files via a signed share link (single-use).
    """
    payload = decode_token(share_token)
    if not payload or payload.get("type") != "share":
        expired_payload = decode_token(share_token, verify_exp=False)
        if expired_payload and expired_payload.get("type") == "share":
            return _render_expired_share_link_page(request=request, payload=expired_payload)

        return HTMLResponse(
            content="Share link is invalid or has expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={
                "Cache-Control": "no-store",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        return HTMLResponse(
            content="Share link is invalid",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
        )

    share_record = ShareLinkRepository(db).get_by_jti(jti)
    if not share_record:
        return HTMLResponse(
            content="Share link is invalid or has expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
        )
    if share_record.used_at is not None:
        return _render_used_share_link_page(request=request, payload=payload)

    raw_document_ids = payload.get("document_ids")
    if raw_document_ids is None and payload.get("document_id") is not None:
        raw_document_ids = [payload.get("document_id")]

    if not raw_document_ids:
        return HTMLResponse(
            content="Share link is invalid or has expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
        )

    document_ids: list[UUID] = []
    for raw_document_id in raw_document_ids:
        try:
            document_ids.append(UUID(str(raw_document_id)))
        except ValueError:
            return HTMLResponse(
                content="Share link is invalid or has expired",
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
            )

    documents = []
    doc_repo = DocumentRepository(db)
    for document_id in document_ids:
        document = doc_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )
        documents.append(document)

    headers = {
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    if len(documents) == 1:
        document = documents[0]
        download_name = _build_download_name(document)
        if _is_remote_file_path(document.file_path):
            return await _stream_remote_file(
                document.file_path,
                filename=download_name,
                jti=jti,
            )

        file_path = Path(document.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found"
            )

        media_type, _ = mimetypes.guess_type(download_name)
        return FileResponse(
            path=file_path,
            media_type=media_type or "application/octet-stream",
            filename=download_name,
            headers=headers,
            background=BackgroundTask(_mark_share_link_used, jti),
        )

    # Multi-file: download remote blobs to temp files then zip.
    file_service = FileService()
    temp_paths: list[str] = []
    zip_sources: list[tuple[str, Document]] = []
    try:
        for doc in documents:
            if _is_remote_file_path(doc.file_path):
                local_path = await file_service.open_as_tempfile(doc.file_path)
                temp_paths.append(local_path)
                zip_sources.append((local_path, doc))
            else:
                zip_sources.append((doc.file_path, doc))

        temp_documents: list[Document] = []
        for path_str, doc in zip_sources:
            # Create a lightweight proxy object with a local file path for zipping.
            proxy = Document(
                id=doc.id,
                title=doc.title,
                description=doc.description,
                file_path=path_str,
                file_size=doc.file_size,
                file_type=doc.file_type,
                owner_id=doc.owner_id,
                is_public=doc.is_public,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
            temp_documents.append(proxy)

        archive_path, archive_name = _create_zip_archive(temp_documents)
    finally:
        for temp_path in temp_paths:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass

    return FileResponse(
        path=archive_path,
        media_type="application/zip",
        filename=archive_name,
        headers=headers,
        background=BackgroundTask(_cleanup_and_mark_used, archive_path, jti),
    )
