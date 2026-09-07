# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: settings.py
# Version: 1.0.0
# Author: Antigravity
# Description: Settings API router for the Electron frontend.
# --------------------------------------------------------------------------------

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from src.extract_app.core.settings_manager import SettingsManager

router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"]
)

# Initialize settings manager
settings_manager = SettingsManager()

@router.get("")
def get_settings() -> Dict[str, Any]:
    """Retrieve all current application settings."""
    try:
        return settings_manager.settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
def update_settings(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update settings and save to disk."""
    try:
        for key, value in updates.items():
            settings_manager.set(key, value)
        return {"status": "success", "message": "Settings updated", "settings": settings_manager.settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
