"""
PREPLINE FastAPI Application Entrypoint (Phase 14)

Initializes FastAPI app, includes API routers, and configures middleware.
"""

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import backend.routes as routes
from backend.routes import router as api_router

# Multipart framing around the file is small; anything this far over the file limit is rejected
# from its Content-Length before the body is read or spooled to disk.
_MULTIPART_OVERHEAD_BYTES = 64 * 1024

app = FastAPI(
    title="PREPLINE — Curriculum-to-Interview Alignment",
    description="Curriculum-to-Interview Alignment Engine (prototype; supported company/role targets in config/targets.json)",
    version="1.1.0"
)

# CORS: only the configured origins (default: the local Streamlit dashboard), never with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=routes.API_CONFIG["cors_allowed_origins"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.middleware("http")
async def reject_oversized_uploads(request: Request, call_next):
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > routes.MAX_UPLOAD_BYTES + _MULTIPART_OVERHEAD_BYTES:
        return JSONResponse(
            status_code=413,
            content={"detail": f"Upload exceeds the {routes.MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."},
        )
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    """Any unhandled error: generic 500 + request id to the client, full traceback to the server log."""
    return routes.internal_error_response(exc, f"{request.method} {request.url.path}")


# Register API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "engine": "PREPLINE",
        "version": "1.1.0",
        "scope": f"Prototype: {routes._target_names()}",
        "status": "RUNNING"
    }


def dev_server_settings() -> dict:
    """Dev server binds to loopback only; set PREPLINE_HOST (e.g. 0.0.0.0) to expose it deliberately."""
    return {
        "host": os.environ.get("PREPLINE_HOST", "127.0.0.1"),
        "port": int(os.environ.get("PREPLINE_PORT", "8000")),
        "reload": True,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", **dev_server_settings())
