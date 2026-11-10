"""FastAPI backend server for the NIDS SOC Command Dashboard."""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from dashboard.backend.config import (
    CORS_ORIGINS,
    DB_PATH,
    FRONTEND_DIST,
    HOST,
    PORT,
)
from dashboard.backend.database import init_db
from dashboard.backend.routes import alerts, flows, sensors, system
from dashboard.backend.ws_manager import ws_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dashboard.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes SQLite database and performs pre-flight checks on startup."""
    logger.info(f"Initializing NIDS SOC database at: {DB_PATH}")
    init_db(DB_PATH)
    logger.info("NIDS SOC backend ready to receive telemetry.")
    yield
    logger.info("Shutting down NIDS SOC backend.")


app = FastAPI(
    title="NIDS SOC Command Dashboard",
    description="Enterprise-grade SOC monitoring and flow triage interface for cascaded NIDS pipeline.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local development and Vue SPA
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers (both /api/dashboard and /api for maximum compatibility)
for prefix in ["/api/dashboard", "/api"]:
    app.include_router(flows.router, prefix=prefix)
    app.include_router(alerts.router, prefix=prefix)
    app.include_router(sensors.router, prefix=prefix)
    app.include_router(system.router, prefix=prefix)


# Real-time WebSockets
@app.websocket("/ws")
@app.websocket("/api/ws")
@app.websocket("/api/dashboard/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry, alert notifications, and heartbeat streaming."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Client heartbeat or command listener
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.debug(f"WebSocket client error: {exc}")
        await ws_manager.disconnect(websocket)


# Mount Static Frontend if compiled
assets_dir = FRONTEND_DIST / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serves the Vue SPA root index.html."""
    index_html = FRONTEND_DIST / "index.html"
    if index_html.exists():
        return FileResponse(index_html)
    return {
        "status": "NIDS SOC Backend Running",
        "message": "Frontend not compiled yet. Run 'npm run build' inside dashboard/frontend/.",
        "api_docs": "/docs",
        "api_init": "/api/dashboard/init",
    }


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """Serves the Vue SPA index.html with client-side routing fallback."""
    # Don't intercept API or WebSocket calls
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json") or full_path == "ws":
        return {"detail": "Not Found"}

    file_candidate = FRONTEND_DIST / full_path
    if file_candidate.is_file():
        return FileResponse(file_candidate)

    index_html = FRONTEND_DIST / "index.html"
    if index_html.exists():
        return FileResponse(index_html)

    return {
        "status": "NIDS SOC Backend Running",
        "message": "Frontend not compiled yet. Run 'npm run build' inside dashboard/frontend/.",
        "api_docs": "/docs",
        "api_init": "/api/dashboard/init",
    }


def main():
    """CLI launcher for the standalone dashboard server."""
    parser = argparse.ArgumentParser(description="Run NIDS SOC Dashboard Backend Server.")
    parser.add_argument("--host", type=str, default=HOST, help=f"Host interface (default: {HOST})")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port (default: {PORT})")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    uvicorn.run("dashboard.backend.server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
