# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: main.py
# Version: 1.0.0
# Author: Antigravity
# Description: FastAPI backend for the Electron UI
# --------------------------------------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ExtractPDF-EPUB API",
    description="Backend API for the Electron frontend",
    version="1.0.0"
)

# Allow CORS for the Electron frontend
from src.extract_app.api.routers import settings, library, ingest, editor

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường dev Electron thường dùng localhost:5173 hoặc file://
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(settings.router)
app.include_router(library.router)
app.include_router(ingest.router)
app.include_router(editor.router)

@app.get("/api/ping")
def ping() -> dict[str, str]:
    """Test endpoint for frontend connectivity."""
    return {"status": "ok", "message": "pong"}

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("API_PORT", os.getenv("PORT", 8000)))
    uvicorn.run("src.extract_app.api.main:app", host="127.0.0.1", port=port, reload=True)
