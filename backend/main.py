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
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# English text backend/ English text sys.path English textEnglish text routes/services English text
sys.path.insert(0, str(Path(__file__).parent))

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

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' https:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
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
    def serve_index() -> FileResponse:
        """English text"""
        return FileResponse(str(FRONTEND_DIR / "index.html"))

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
