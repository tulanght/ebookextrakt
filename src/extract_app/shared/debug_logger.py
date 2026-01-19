
import sys
from pathlib import Path

LOG_FILE = Path("ui_test_log.txt")

def log(msg: str):
    """
    Logs a message to stdout and appends it to ui_test_log.txt
    """
    try:
        # 1. Print to console (handle encoding issues gently)
        try:
            print(f"[LOG] {msg}")
        except UnicodeEncodeError:
            # Fallback for chars that console can't display
            print(f"[LOG] {msg.encode('utf-8', errors='replace').decode('utf-8')}")
            
        # 2. Append to file
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
    except Exception as e:
        print(f"!! LOGGING ERROR: {e}")

def clear_log():
    """Clears the log file."""
    if LOG_FILE.exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("=== LOG STARTED ===\n")
