from __future__ import annotations

import os
import socket
from pathlib import Path
import secrets
import traceback
import logging

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

def _log_path(app_data_dir: Path) -> Path:
    logs_dir = app_data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir / "server.log"


def main() -> None:
    # Persist data in a writable folder (so it works when installed to Program Files).
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

    requested_port = int(os.environ.get("API_PORT") or 0) or 0

    port_file = Path(os.environ.get("PORT_FILE") or (app_data_dir / "port.txt"))
    try:
        port_file.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        # best effort
        pass

    log_file = _log_path(app_data_dir)

    try:
        # Ensure log starts clean for each run.
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.write_text("", encoding="utf-8")
        except Exception:
            pass

        # Route uvicorn logs to the same file for easier debugging.
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            handlers=[logging.FileHandler(log_file, encoding="utf-8", mode="w")],
        )

        # Bind a socket first so we can reliably know the actual port (including when requested_port=0).
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("127.0.0.1", requested_port))
        server_socket.listen(128)

        effective_port = int(server_socket.getsockname()[1])
        os.environ["API_PORT"] = str(effective_port)
        try:
            port_file.write_text(str(effective_port), encoding="utf-8")
        except Exception:
            pass

        logging.getLogger("link1die.desktop").info("Started on 127.0.0.1:%s", effective_port)

        # Force-import dynamically loaded crypto handlers so PyInstaller bundles them.
        import passlib.handlers.pbkdf2  # noqa: F401

        # IMPORTANT: import the ASGI app so PyInstaller bundles the `app` package.
        from app.desktop_app import app as asgi_app

        config = uvicorn.Config(
            asgi_app,
            host="127.0.0.1",
            port=effective_port,
            reload=False,
            log_level="info",
            proxy_headers=True,
            forwarded_allow_ips="*",
            access_log=False,
        )
        server = uvicorn.Server(config)
        server.run(sockets=[server_socket])
    except Exception:
        try:
            with log_file.open("a", encoding="utf-8") as handle:
                handle.write("\n")
                handle.write(traceback.format_exc())
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
