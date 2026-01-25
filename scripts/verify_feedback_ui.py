# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: scripts/verify_feedback_ui.py
# Version: 1.0.0
# Author: Antigravity
# Description: Verifies instantiation and basic API of new UI components.
# --------------------------------------------------------------------------------

import sys
import os
import customtkinter as ctk

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from extract_app.modules.ui.log_panel import LogPanel
    from extract_app.modules.ui.loading_overlay import LoadingOverlay
    from extract_app.shared import debug_logger
    
    print("Success: Imported UI modules.")

    # Setup dummy root
    root = ctk.CTk()
    
    # Test LogPanel
    print("Testing LogPanel...")
    panel = LogPanel(root)
    panel.pack()
    panel.write_log("Test log message")
    panel.clear_logs()
    print("Pass: LogPanel basic methods.")

    # Test Logger Integration
    print("Testing Debug Logger Observer...")
    received = []
    def callback(msg):
        received.append(msg)
    
    debug_logger.register_listener(callback)
    debug_logger.log("Observer Test")
    
    if "Observer Test" in received:
        print("Pass: Logger observer pattern.")
    else:
        raise AssertionError("Logger observer failed to notify.")
    
    debug_logger.unregister_listener(callback)

    # Test LoadingOverlay
    print("Testing LoadingOverlay...")
    overlay = LoadingOverlay(root)
    overlay.update_status(title="Testing", progress=0.5)
    overlay.update_status(progress=None) # Indeterminate
    print("Pass: LoadingOverlay API.")

    print("ALL TESTS PASSED.")
    # root.destroy() # Might hang on some CI/headless, but useful here/
    
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
