from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.services.seed_service import seed_admin_user


def _resolve_web_dist_dir() -> Path:
    """Resolve the bundled React build directory."""
    configured = getattr(settings, "WEB_DIST_DIR", None)
    if configured:
        return Path(str(configured)).resolve()

    # Default for local dev / packaging: backend/web_dist
    return (Path(__file__).resolve().parents[1] / "web_dist").resolve()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.PROJECT_DESCRIPTION,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS or ["*"],
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "ok"}

    @app.on_event("startup")
    def startup_event() -> None:
        init_db()
        db = SessionLocal()
        try:
            seed_admin_user(db)
        finally:
            db.close()

    web_dist_dir = _resolve_web_dist_dir()
    index_file = web_dist_dir / "index.html"

    if web_dist_dir.exists():
        app.mount(
            "/",
            StaticFiles(directory=str(web_dist_dir), html=True),
            name="web",
        )

        # React-router fallback (so /login works when opened directly).
        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str):  # noqa: ARG001
            if index_file.exists():
                return FileResponse(index_file)
            return {"error": "web_dist is missing index.html"}

    return app


app = create_app()
