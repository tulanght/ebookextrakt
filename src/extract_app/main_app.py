# file-path: src/extract_app/main_app.py
# version: 2.1 (Pylint Compliance)
# last-updated: 2025-09-26
# description: Cleans up the app dispatcher to meet Pylint standards.

"""
Application Dispatcher.

This module contains the main function that initializes and runs the
application's main window.
"""

from .modules.main_window import MainWindow


def main():
    """Initializes and runs the main application window."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()