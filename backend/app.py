"""
Vercel entrypoint.

Vercel auto-detects FastAPI apps when an `app` object is exported at the project root.
"""

from app.main import app  # noqa: F401

