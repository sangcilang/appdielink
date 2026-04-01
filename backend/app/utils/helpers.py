"""
Helper Functions and Utilities
"""
from typing import Any
from uuid import UUID
import re

def is_valid_uuid(value: str) -> bool:
    """Check if string is valid UUID"""
    try:
        UUID(value)
        return True
    except ValueError:
        return False

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:
    """Remove special characters from filename"""
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', filename)

def format_file_size(size_bytes: int) -> str:
    """Format bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def pagination_params(skip: int = 0, limit: int = 100) -> tuple[int, int]:
    """Validate pagination parameters"""
    skip = max(0, skip)
    limit = min(max(1, limit), 1000)  # Max 1000 items per page
    return skip, limit
