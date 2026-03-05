# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/glossary_manager.py
# Version: 1.0.0
# Author: Antigravity
# Description: Manages user-defined translations and terminology.
# --------------------------------------------------------------------------------

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

class GlossaryManager:
    """
    Manages user-defined glossary terms categorize by subject.
    Data is stored in user_data/glossary.json.
    """
    
    DEFAULT_DATA = {
        "active_category": "General",
        "categories": {
            "General": {}
        }
    }

    def __init__(self, data_path: str = "user_data/glossary.json"):
        self.data_path = Path(data_path)
        self.data: Dict = self.DEFAULT_DATA.copy()
        self._load_data()

    def _load_data(self):
        """Load glossary data from JSON."""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    # Merge with default to ensure structure
                    if "active_category" in file_data:
                        self.data["active_category"] = file_data["active_category"]
                    if "categories" in file_data:
                        for cat, terms in file_data["categories"].items():
                            if cat not in self.data["categories"]:
                                self.data["categories"][cat] = {}
                            self.data["categories"][cat].update(terms)
            except Exception as e:
                print(f"[GlossaryManager] Error loading data: {e}")
        else:
            self._save_data()

    def _save_data(self):
        """Save glossary data to JSON."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[GlossaryManager] Error saving data: {e}")

    # --- Category Management ---
    
    def get_categories(self) -> List[str]:
        """Return list of all category names."""
        return list(self.data["categories"].keys())

    def get_active_category(self) -> str:
        """Return the currently active category name."""
        return self.data.get("active_category", "General")

    def set_active_category(self, category: str) -> bool:
        """Set the active category. Returns True if category exists."""
        if category in self.data["categories"]:
            self.data["active_category"] = category
            self._save_data()
            return True
        return False

    def add_category(self, category: str):
        """Create a new empty category."""
        if category and category not in self.data["categories"]:
            self.data["categories"][category] = {}
            self._save_data()

    def delete_category(self, category: str) -> bool:
        """Delete a category. Cannot delete General or currently active category."""
        if category == "General" or category == self.get_active_category():
            return False
        if category in self.data["categories"]:
            del self.data["categories"][category]
            self._save_data()
            return True
        return False


    # --- Term Management ---

    def get_terms(self, category: str = None) -> Dict[str, str]:
        """Get all terms for a category (defaults to active category)."""
        cat = category or self.get_active_category()
        return self.data["categories"].get(cat, {})

    def add_term(self, en_term: str, vi_term: str, category: str = None):
        """Add or update a single term in the specified category."""
        if not en_term or not vi_term:
            return
        cat = category or self.get_active_category()
        if cat not in self.data["categories"]:
            self.add_category(cat)
        
        self.data["categories"][cat][en_term.strip()] = vi_term.strip()
        self._save_data()

    def delete_term(self, en_term: str, category: str = None):
        """Remove a term from the specified category."""
        cat = category or self.get_active_category()
        if cat in self.data["categories"] and en_term in self.data["categories"][cat]:
            del self.data["categories"][cat][en_term]
            self._save_data()

    # --- Prompt Injection ---

    def get_active_glossary_string(self) -> str:
        """
        Serialize the active category into a string suitable for LLM injection.
        Example: "habitat -> môi trường sống"
        """
        terms = self.get_terms()
        if not terms:
            return ""
        
        lines = []
        for en, vi in terms.items():
            lines.append(f"'{en}' : '{vi}'")
            
        return "\n".join(lines)
