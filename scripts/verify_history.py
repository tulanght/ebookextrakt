# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: scripts/verify_history.py
# Version: 1.0.0
# Author: Antigravity
# Description: Verifies HistoryManager persistence and logic.
# --------------------------------------------------------------------------------

import sys
import os
import shutil
import json
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from extract_app.core.history_manager import HistoryManager
    
    # Setup test env
    TEST_DIR = Path("test_user_data")
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
        
    print("Testing HistoryManager...")
    manager = HistoryManager(storage_dir=str(TEST_DIR), filename="test_history.json")
    
    # 1. Add Entry
    manager.add_entry("C:/Books/Book1.epub", "Book One")
    hist = manager.load_history()
    assert len(hist) == 1
    assert hist[0]['title'] == "Book One"
    print("Pass: Add Entry")
    
    # 2. Add Duplicate (Should move to top)
    manager.add_entry("C:/Books/Book2.epub", "Book Two")
    manager.add_entry("C:/Books/Book1.epub", "Book One") # Re-add 1
    hist = manager.load_history()
    assert len(hist) == 2
    assert hist[0]['title'] == "Book One" # Moved to top
    print("Pass: Duplicate Handling")

    # 3. Persistence
    manager2 = HistoryManager(storage_dir=str(TEST_DIR), filename="test_history.json")
    hist2 = manager2.load_history()
    assert len(hist2) == 2
    print("Pass: Persistence")
    
    # 4. Remove
    manager.remove_entry("C:/Books/Book1.epub")
    hist = manager.load_history()
    assert len(hist) == 1
    assert hist[0]['title'] == "Book Two"
    print("Pass: Remove Entry")
    
    # Cleanup
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
        
    print("ALL TESTS PASSED.")
    
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
