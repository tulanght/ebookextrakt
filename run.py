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
from extract_app.main_app import main

if __name__ == "__main__":
    main()