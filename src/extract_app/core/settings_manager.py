# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/settings_manager.py
# Version: 1.0.0
# Author: Antigravity
# Description: Manages user configuration and secrets.
# --------------------------------------------------------------------------------

import json
from pathlib import Path
from typing import Dict, Any, Optional

class SettingsManager:
    """
    Handles loading and saving of application settings (user_data/settings.json).
    """
    
    DEFAULT_SETTINGS = {
        "gemini_api_key": "",
        "theme": "Dark",
        "default_output_dir": ""
    }

    def __init__(self, settings_path: str = "user_data/settings.json"):
        self.settings_path = Path(settings_path)
        self.settings: Dict[str, Any] = self.DEFAULT_SETTINGS.copy()
        self._load_settings()

    def _load_settings(self):
        """Loads settings from JSON file if exists."""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Merge with default to ensure all keys exist
                    self.settings.update(data)
            except Exception as e:
                print(f"Error loading settings: {e}")
        else:
            self._save_settings()

    def _save_settings(self):
        """Saves current settings to JSON file."""
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        self.settings[key] = value
        self._save_settings()

    def get_api_key(self) -> str:
        return self.settings.get("gemini_api_key", "")

    def set_api_key(self, api_key: str):
        self.set("gemini_api_key", api_key)
