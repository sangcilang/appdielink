from __future__ import annotations

import os
import socket
from pathlib import Path
import secrets
import webbrowser

import uvicorn


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _get_app_data_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Link1Die"
    return Path.home() / ".link1die"


def main() -> None:
    # Persist data in a writable folder (so the EXE can run from Program Files).
    app_data_dir = _get_app_data_dir()
    app_data_dir.mkdir(parents=True, exist_ok=True)

    uploads_dir = app_data_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = f"sqlite:///{(app_data_dir / 'link1die.db').as_posix()}"
    if "UPLOAD_DIR" not in os.environ:
        os.environ["UPLOAD_DIR"] = str(uploads_dir)
    if "SECRET_KEY" not in os.environ:
        os.environ["SECRET_KEY"] = secrets.token_urlsafe(48)
    if "CORS_ORIGINS" not in os.environ:
        os.environ["CORS_ORIGINS"] = '["http://127.0.0.1","http://localhost"]'

    port = int(os.environ.get("API_PORT") or 0) or _pick_free_port()
    url = f"http://127.0.0.1:{port}/"

    # Open the UI in the default browser.
    webbrowser.open(url)

    uvicorn.run(
        "app.desktop_app:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()

