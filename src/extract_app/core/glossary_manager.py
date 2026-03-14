# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/glossary_manager.py
# Version: 1.0.0
# Author: Antigravity
# Description: Manages user-defined translations and terminology.
# --------------------------------------------------------------------------------

import json
import os
import copy
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

    def __init__(self, data_path: str = None):
        if data_path is None:
            from .config import get_user_data_dir
            self.data_path = get_user_data_dir() / "glossary.json"
        else:
            self.data_path = Path(data_path)
        self.data: Dict = copy.deepcopy(self.DEFAULT_DATA)  # Deep copy avoids shared state
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

    def bulk_add_terms(self, terms_dict: Dict[str, str], category: str = None) -> int:
        """Add multiple terms efficiently with a single disk write. Returns number of new terms added."""
        if not terms_dict:
            return 0
            
        cat = category or self.get_active_category()
        if cat not in self.data["categories"]:
            self.data["categories"][cat] = {}
            
        added_count = 0
        existing_terms = self.data["categories"][cat]
        
        for en, vi in terms_dict.items():
            en_clean = en.strip()
            vi_clean = vi.strip()
            if en_clean and vi_clean and en_clean not in existing_terms:
                existing_terms[en_clean] = vi_clean
                added_count += 1
                
        if added_count > 0:
            self._save_data()
            
        return added_count

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
        Returns ALL terms — use get_relevant_glossary_string() for filtered injection.
        """
        terms = self.get_terms()
        if not terms:
            return ""
        
        lines = []
        for en, vi in terms.items():
            lines.append(f"'{en}' → '{vi}'")
            
        return "\n".join(lines)

    def get_relevant_glossary_string(self, source_text: str) -> str:
        """
        Filter active glossary to only include terms that appear in source_text.
        Uses case-insensitive word-boundary matching for accuracy.
        
        This is critical for Local LLM (TranslateGemma 12B) which has limited
        context (4096 tokens). Injecting 100+ terms wastes precious tokens;
        typically only 5-15 terms are relevant per chunk of 1500 chars.
        
        Args:
            source_text: The chunk of text that will be translated.
            
        Returns:
            Formatted glossary string with only matching terms, or empty string.
        """
        import re
        
        terms = self.get_terms()
        if not terms or not source_text:
            return ""
        
        text_lower = source_text.lower()
        matched_lines = []
        
        for en, vi in terms.items():
            en_lower = en.lower()
            # Use word boundary matching to avoid partial matches
            # e.g., "sow" should not match "Moscow"
            # For multi-word terms, check if the exact phrase exists
            try:
                pattern = r'\b' + re.escape(en_lower) + r'\b'
                if re.search(pattern, text_lower):
                    matched_lines.append(f"{en} → {vi}")
            except re.error:
                # Fallback to simple substring check for unusual terms
                if en_lower in text_lower:
                    matched_lines.append(f"{en} → {vi}")
        
        return "\n".join(matched_lines)
