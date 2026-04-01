"""
File Management Service
"""
import os
from pathlib import Path
import tempfile
from uuid import UUID, uuid4

from app.core.config import settings

class FileService:
    """Service for file operations"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.blob_access = getattr(settings, "BLOB_ACCESS", "private")

        # Only create local upload folders when using filesystem storage.
        # On Vercel, the filesystem is read-only except /tmp, and we prefer Blob storage anyway.
        if not self._blob_enabled():
            self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _blob_enabled(self) -> bool:
        return bool(os.environ.get("BLOB_READ_WRITE_TOKEN"))

    def _is_remote_path(self, file_path: str) -> bool:
        return file_path.startswith("http://") or file_path.startswith("https://")
    
    async def save_file(self, user_id: UUID, filename: str, content: bytes) -> str:
        """Save uploaded file to storage"""
        safe_filename = Path(filename).name
        suffix = Path(safe_filename).suffix.lower()
        stored_filename = f"{uuid4().hex}{suffix}"

        if self._blob_enabled():
            from vercel.blob import AsyncBlobClient

            async with AsyncBlobClient() as client:
                blob = await client.put(
                    f"uploads/{user_id}/{stored_filename}",
                    content,
                    access=self.blob_access,
                    add_random_suffix=False,
                )
                return str(blob.url)

        # Local filesystem fallback (dev / desktop)
        user_dir = self.upload_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        file_path = user_dir / stored_filename
        file_path.write_bytes(content)
        return str(file_path)
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        try:
            if self._blob_enabled() and self._is_remote_path(file_path):
                from vercel.blob import AsyncBlobClient

                async with AsyncBlobClient() as client:
                    await client.delete([file_path])
                return True

            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    async def open_as_tempfile(self, file_path: str) -> str:
        """Ensure the file exists on disk and return its local path.

        For remote blob URLs, it downloads into a temp file.
        """
        if not (self._blob_enabled() and self._is_remote_path(file_path)):
            return file_path

        from vercel.blob import AsyncBlobClient

        async with AsyncBlobClient() as client:
            result = await client.get(file_path, access=self.blob_access)
            if result is None or result.status_code != 200 or result.stream is None:
                raise FileNotFoundError("Remote file not found")

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name

            with open(tmp_path, "wb") as handle:
                async for chunk in result.stream:
                    handle.write(chunk)

            return tmp_path
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0
    
    def validate_file(self, filename: str, file_size: int) -> tuple[bool, str]:
        """Validate file before upload"""
        safe_filename = Path(filename).name

        # Check file size
        if file_size > settings.MAX_FILE_SIZE:
            return False, f"File size exceeds {settings.MAX_FILE_SIZE} bytes"
        
        # Check file type
        if "." not in safe_filename:
            return False, "File must have an extension"

        file_ext = safe_filename.rsplit(".", 1)[-1].lower()
        if file_ext not in settings.ALLOWED_FILE_TYPES:
            return False, f"File type .{file_ext} not allowed"
        
        return True, "OK"
