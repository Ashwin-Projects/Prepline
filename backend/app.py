"""
PREPLINE FastAPI Application Entrypoint (Phase 14)

Initializes FastAPI app, includes API routers, and configures middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import router as api_router

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
