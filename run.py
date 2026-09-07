# file-path: run.py
# version: 1.1 (Pylint Compliance)
# last-updated: 2025-09-26
# description: Cleans up the main entry point to meet Pylint standards.

"""
Main entry point for the ExtractPDF-EPUB application.

This script configures the system path to include the 'src' directory
and then launches the main application function.
"""

import sys
from pathlib import Path

# Thêm thư mục src vào Python Path để có thể import các module
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

# pylint: disable=wrong-import-position

# ── Workaround: CustomTkinter 5.2.2 bug ────────────────────────────────────
# _windows_set_titlebar_color() can TclError crash on some Windows configs
# when wm/winfo commands are called during mainloop startup.
# Suppress silently so the app still loads correctly.
import customtkinter.windows.ctk_tk as _ctk_tk

_orig_titlebar = _ctk_tk.CTk._windows_set_titlebar_color

def _safe_set_titlebar_color(self, *args, **kwargs):
    """Patched version that silently ignores TclErrors."""
    try:
        _orig_titlebar(self, *args, **kwargs)
    except Exception:  # noqa: BLE001 — suppress TclError from destroyed state
        pass

_ctk_tk.CTk._windows_set_titlebar_color = _safe_set_titlebar_color
# ───────────────────────────────────────────────────────────────────────────

from extract_app.main_app import main

if __name__ == "__main__":
    main()