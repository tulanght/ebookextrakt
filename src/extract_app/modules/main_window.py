# file-path: src/extract_app/modules/main_window.py
# version: 1.0
# last-updated: 2025-09-16
# description: Định nghĩa class MainWindow, là cửa sổ chính của ứng dụng.

import customtkinter as ctk
import sv_ttk

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ExtractPDF-EPUB App")
        self.geometry("800x600")

        # Áp dụng theme hiện đại sv-ttk
        sv_ttk.set_theme("light")

        self._create_widgets()

    def _create_widgets(self):
        """Tạo các widget con cho cửa sổ chính."""
        # Hiện tại để trống, sẽ được thêm vào trong các bước tiếp theo
        label = ctk.CTkLabel(self, text="Main Application Window")
        label.pack(pady=20, padx=20)