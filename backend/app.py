"""
PREPLINE FastAPI Application Entrypoint (Phase 14)

Initializes FastAPI app, includes API routers, and configures middleware.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import backend.routes as routes
from backend.routes import router as api_router

# Multipart framing around the file is small; anything this far over the file limit is rejected
# from its Content-Length before the body is read or spooled to disk.
_MULTIPART_OVERHEAD_BYTES = 64 * 1024

app = FastAPI(
    title="PREPLINE API Engine",
    description="Curriculum-to-Interview Alignment Engine (Amazon SDE-1 Prototype)",
    version="1.1.0"
)

# Configure CORS for Dashboard/Frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# Register API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "engine": "PREPLINE",
        "version": "1.1.0",
        "scope": "Amazon SDE-1 Prototype",
        "status": "RUNNING"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
