# file-path: src/extract_app/modules/main_window.py
# version: 2.0
# last-updated: 2025-09-16
# description: Định nghĩa class MainWindow, chứa giao diện chính của ứng dụng.

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
        # Cấu hình grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Dành không gian cho khu vực kết quả sau này

        # --- KHUNG CHỌN FILE ---
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        select_button = ctk.CTkButton(input_frame, text="Chọn File Ebook...", command=self._on_select_file_button_click)
        select_button.grid(row=0, column=0, padx=10, pady=10)

        self.selected_file_label = ctk.CTkLabel(input_frame, text="Chưa có file nào được chọn.", anchor="w")
        self.selected_file_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    
    def _on_select_file_button_click(self):
        """Xử lý sự kiện khi nút 'Chọn File Ebook...' được nhấn."""
        print("Nút chọn file đã được nhấn!")
        # Logic mở hộp thoại chọn file sẽ được thêm ở đây