"""FounderOS FastAPI application.

PostgreSQL is the runtime datastore; DATABASE_URL must be configured.
  2. English text 6 English text API English text
  3. English textfrontend/
  4. English text 8010 English text

English text
    python main.py
    English text uvicorn main:app --reload --port 8010
"""

import hashlib
import hmac
import os
import secrets
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# English text backend/ English text sys.path English textEnglish text routes/services English text
from backend import db  # noqa: E402
from backend.db import init_db  # noqa: E402
from backend.routes import archive, auth, chat, config_api, decision, graph, modes, stats, tts  # noqa: E402

# English textchoice-skill/frontend/
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
FRONTEND_V2_DIR = FRONTEND_DIR / "v2" / "dist"

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

    # Once authenticated, the workspace cookie is only valid for workspaces
    # owned by that account. On login, move the browser to the user's latest
    # workspace instead of ever exposing another user's graph.
    auth_user_id = db.get_user_id_from_auth_token(request.cookies.get("founderos_auth"))
    if auth_user_id and not db.workspace_owned_by_user(workspace_id, auth_user_id):
        owned = db.get_user_workspaces(auth_user_id)
        if owned:
            workspace_id = owned[0]["workspaceId"]
            new_cookie = True
        else:
            db.claim_workspace_for_user(workspace_id, auth_user_id)

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
app.include_router(auth.router)
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
    """Return API and database health."""
    db.healthcheck()
    return {"name": "FounderOS API", "status": "ok", "database": "postgresql", "version": "0.9.1"}



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
        return FileResponse(str(FRONTEND_V2_DIR / "index.html") if (FRONTEND_V2_DIR / "index.html").exists() else str(FRONTEND_DIR / "index.html"))

    @app.get("/app/style.css")
    def serve_v2_style() -> FileResponse:
        return FileResponse(str(FRONTEND_V2_DIR / "style.css"))

    @app.get("/app/assets/{asset_path:path}")
    def serve_v2_asset(asset_path: str) -> FileResponse:
        return FileResponse(str(FRONTEND_V2_DIR / "assets" / asset_path))

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