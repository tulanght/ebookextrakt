# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: scripts/verify_startup.py
# Version: 1.0.0
# Author: Antigravity
# Description: Verifies that the MainWindow can be initialized without errors.
# --------------------------------------------------------------------------------

import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from extract_app.modules.main_window import MainWindow
    print("Successfully imported MainWindow.")
    
    # Initialize without showing (headless check)
    # Note: Requires display, but we can verify imports and init logic until mainloop
    app = MainWindow()
    print("Successfully initialized MainWindow instance.")
    
    # Check if Sidebar has new attributes
    if hasattr(app.sidebar, 'show_active_book_controls'):
        print("Verified Sidebar: show_active_book_controls exists.")
    else:
        raise AttributeError("Sidebar missing show_active_book_controls")
        
    app.destroy()
    print("Startup verification passed.")
    
except Exception as e:
    print(f"Startup verification failed: {e}")
    sys.exit(1)
