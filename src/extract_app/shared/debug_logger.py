# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/shared/debug_logger.py
# Version: 1.1.0
# Author: Antigravity
# Description: Enhanced logger with UI callback support (Observer pattern).
# --------------------------------------------------------------------------------

import sys
from pathlib import Path
from typing import Callable, List

LOG_FILE = Path("ui_test_log.txt")

# List of callback functions to notify on new log message
_listeners: List[Callable[[str], None]] = []

def register_listener(callback: Callable[[str], None]):
    """Register a function to be called when a log message is emitted."""
    if callback not in _listeners:
        _listeners.append(callback)

def unregister_listener(callback: Callable[[str], None]):
    """Unregister a listener."""
    if callback in _listeners:
        _listeners.remove(callback)

def log(msg: str):
    """
    Logs a message to stdout, appends it to file, and notifies listeners.
    """
    try:
        # 1. Print to console (handle encoding issues gently)
        try:
            print(f"[LOG] {msg}")
        except UnicodeEncodeError:
            # Handle surrogates and other unprintable chars safely
            safe_msg = msg.encode(sys.stdout.encoding or 'utf-8', errors='backslashreplace').decode(sys.stdout.encoding or 'utf-8')
            print(f"[LOG] {safe_msg}")
            
        # 2. Append to file
        with open(LOG_FILE, "a", encoding="utf-8", errors="backslashreplace") as f:
            f.write(f"{msg}\n")
            
        # 3. Notify Listeners (UI)
        for listener in _listeners:
            try:
                listener(msg)
            except Exception as e:
                print(f"!! LISTENER ERROR: {e}")
                
    except Exception as e:
        print(f"!! LOGGING ERROR: {e}")

def clear_log():
    """Clears the log file."""
    if LOG_FILE.exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("=== LOG STARTED ===\n")
