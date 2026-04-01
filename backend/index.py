"""
Vercel entrypoint.

Expose the FastAPI `app` at module top-level so `@vercel/python` can serve it.
"""

from app.main import app  # noqa: F401

