# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/history_manager.py
# Version: 1.0.0
# Author: Antigravity
# Description: Manages the history of opened/extracted files.
# --------------------------------------------------------------------------------

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class HistoryManager:
    """
    Manages user history (recently opened files).
    Stores data in user_data/history.json.
    """
    def __init__(self, storage_dir: str = "user_data", filename: str = "history.json", max_items: int = 10):
        self.storage_dir = Path(storage_dir)
        self.history_file = self.storage_dir / filename
        self.max_items = max_items
        self._ensure_storage()

    def _ensure_storage(self):
        """Ensure the storage directory exists."""
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True, exist_ok=True)

    def load_history(self) -> List[Dict]:
        """Load history from JSON file."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Sort by last_opened descending just in case
                data.sort(key=lambda x: x.get('last_opened', ''), reverse=True)
                return data
        except (json.JSONDecodeError, IOError):
            return []

    def add_entry(self, filepath: str, title: str = None, status: str = "opened"):
        """
        Add or update an entry in the history.
        Moves existing entry to top if duplicate filepath.
        """
        history = self.load_history()
        
        # Normalize path
        filepath = str(Path(filepath).resolve())
        if not title:
            title = Path(filepath).name

        new_entry = {
            "filepath": filepath,
            "title": title,
            "last_opened": datetime.now().isoformat(),
            "status": status
        }

        # Remove existing if present (to move to top)
        history = [item for item in history if item['filepath'] != filepath]
        
        # Add new to top
        history.insert(0, new_entry)
        
        # Trim
        if len(history) > self.max_items:
            history = history[:self.max_items]
            
        self._save_history(history)

    def _save_history(self, history: List[Dict]):
        """Save history list to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving history: {e}")

    def clear_history(self):
        """Clear all history."""
        self._save_history([])

    def remove_entry(self, filepath: str):
        """Remove a specific entry."""
        history = self.load_history()
        filepath = str(Path(filepath).resolve())
        history = [item for item in history if item['filepath'] != filepath]
        self._save_history(history)
