"""
Load API keys before other app modules read os.environ.

Docker mounts only ./backend at /app, so a project-root .env is not on disk inside the
container unless you bind-mount it. A file backend/.env is visible as /app/.env.

Compose may set OPENAI_API_KEY= / SERPER_API_KEY= to empty strings when the host has no
.env next to docker-compose.yml. python-dotenv(load_dotenv) does not override existing
keys unless override=True — so we always use override=True here.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    app_root = Path(__file__).resolve().parent.parent
    # backend/.env → /app/.env in Docker (included in ./backend volume mount)
    if (app_root / ".env").is_file():
        load_dotenv(app_root / ".env", override=True)
        logger.info(
            "Loaded %s (serper=%s openai=%s)",
            app_root / ".env",
            bool((os.getenv("SERPER_API_KEY") or "").strip()),
            bool((os.getenv("OPENAI_API_KEY") or "").strip()),
        )
    # Local dev: repo root .env (parent of backend/). Skip if app_root is /app (parent is /).
    parent = app_root.parent
    if parent != Path("/") and (parent / ".env").is_file():
        load_dotenv(parent / ".env", override=False)
        logger.info(
            "Merged %s (serper=%s openai=%s)",
            parent / ".env",
            bool((os.getenv("SERPER_API_KEY") or "").strip()),
            bool((os.getenv("OPENAI_API_KEY") or "").strip()),
        )
