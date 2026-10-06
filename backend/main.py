"""English text - FastAPI English text

English text
  1. English text SQLitechoice.db
  2. English text 6 English text API English text
  3. English textfrontend/
  4. English text 8010 English text

English text
    python main.py
    English text uvicorn main:app --reload --port 8010
"""

import sys
import hashlib
import hmac
import os
import secrets
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# English text backend/ English text sys.path English textEnglish text routes/services English text
sys.path.insert(0, str(Path(__file__).parent))

import db  # noqa: E402
from db import init_db  # noqa: E402
from routes import archive, chat, config_api, decision, graph, modes, stats, tts  # noqa: E402

# English textchoice-skill/frontend/
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# English text
init_db()

app = FastAPI(
    title="English text API",
    description="English textEnglish text",
    version="0.9.1",
)

_SESSION_COOKIE = "founderos_workspace"
_SESSION_MAX_AGE = 60 * 60 * 24 * 365
_SESSION_SECRET = os.environ.get("FOUNDEROS_SESSION_SECRET") or os.environ.get("SECRET_KEY") or "founderos-development-session-secret"


def _sign_workspace(raw: str) -> str:
    sig = hmac.new(_SESSION_SECRET.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return raw + "." + sig


def _verify_workspace(value: Optional[str]) -> Optional[str]:
    if not value or "." not in value:
        return None
    raw, sig = value.rsplit(".", 1)
    if not raw or not sig:
        return None
    expected = hmac.new(_SESSION_SECRET.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    return raw


@app.middleware("http")
async def security_headers(request: Request, call_next):
    raw_cookie = request.cookies.get(_SESSION_COOKIE)
    workspace_id = _verify_workspace(raw_cookie)
    new_cookie = False
    if not workspace_id:
        workspace_id = secrets.token_urlsafe(24)
        new_cookie = True

    token = db.set_workspace_id(workspace_id)
    try:
        response = await call_next(request)
    finally:
        db.reset_workspace_id(token)

    if new_cookie:
        response.set_cookie(
            _SESSION_COOKIE,
            _sign_workspace(workspace_id),
            max_age=_SESSION_MAX_AGE,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
            path="/",
        )

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' https:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    elif request.url.path.startswith("/scripts/") or request.url.path.startswith("/styles/") or request.url.path in ("/", "/app"):
        response.headers["Cache-Control"] = "no-cache, private, must-revalidate"
    return response

# ─── API English text ───────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(graph.router)
app.include_router(modes.router)
app.include_router(decision.router)
app.include_router(archive.router)
app.include_router(stats.router)
app.include_router(config_api.router)
app.include_router(tts.router)


# ─── English text ───────────────────────────────────────────────────


@app.get("/api/health")
def health() -> dict:
    """English text"""
    return {"name": "English text API", "status": "ok", "version": "0.9.1"}


# ─── English text ──────────────────────────────────────────────
# English text frontend/ English textCLI-only English text
if FRONTEND_DIR.exists():
    styles_dir = FRONTEND_DIR / "styles"
    scripts_dir = FRONTEND_DIR / "scripts"
    assets_dir = FRONTEND_DIR / "assets"

    if styles_dir.exists():
        app.mount("/styles", StaticFiles(directory=str(styles_dir)), name="styles")
    if scripts_dir.exists():
        app.mount("/scripts", StaticFiles(directory=str(scripts_dir)), name="scripts")
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    def serve_landing() -> FileResponse:
        """Public introduction page. The graph workspace lives at /app."""
        return FileResponse(str(FRONTEND_DIR / "landing.html"))

    @app.get("/app")
    def serve_workspace() -> FileResponse:
        """The graph-first FounderOS workspace."""
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/app/")
    def serve_workspace_slash() -> RedirectResponse:
        # relative asset URLs in index.html only resolve from /app, never /app/
        return RedirectResponse("/app", status_code=308)

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str) -> FileResponse:
        """SPA fallbackEnglish text API English text index.html"""
        # English text /api/ English text
        if full_path.startswith("api/"):
            return FileResponse(str(FRONTEND_DIR / "index.html"), status_code=404)
        # English text
        candidate = FRONTEND_DIR / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        # fallback English text index.html
        return FileResponse(str(FRONTEND_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8010)