# file-path: src/extract_app/main_app.py
# version: 2.0
# last-updated: 2025-09-16
# description: File điều phối chính của ứng dụng, khởi tạo và chạy MainWindow.

from .modules.main_window import MainWindow

def main():
    """Hàm chính để khởi chạy ứng dụng."""
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()