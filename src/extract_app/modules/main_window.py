# file-path: src/extract_app/modules/main_window.py
# version: 2.2
# last-updated: 2025-09-17
# description: Cập nhật để gọi parser xử lý file sau khi chọn.

import customtkinter as ctk
from customtkinter import filedialog
import sv_ttk
from pathlib import Path

# Import tương đối từ package 'core'
from ..core import pdf_parser

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ExtractPDF-EPUB App")
        self.geometry("800x600")
        sv_ttk.set_theme("light")
        self._create_widgets()

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        select_button = ctk.CTkButton(input_frame, text="Chọn File Ebook...", command=self._on_select_file_button_click)
        select_button.grid(row=0, column=0, padx=10, pady=10)

        self.selected_file_label = ctk.CTkLabel(input_frame, text="Chưa có file nào được chọn.", anchor="w")
        self.selected_file_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    def _on_select_file_button_click(self):
        file_types = [("Ebook files", "*.pdf *.epub"), ("All files", "*.*")]
        filepath = filedialog.askopenfilename(title="Chọn một file Ebook", filetypes=file_types)
        
        if not filepath:
            print("Không có file nào được chọn.")
            return

        self.selected_file_label.configure(text=filepath)
        print(f"File đã chọn: {filepath}")

        # Phân loại và xử lý file
        file_extension = Path(filepath).suffix.lower()
        if file_extension == ".pdf":
            print("\n--- Bắt đầu trích xuất PDF ---")
            extracted_text = pdf_parser.extract_text_from_pdf(filepath)
            print(extracted_text)
            print("--- Hoàn tất trích xuất PDF ---\n")
        elif file_extension == ".epub":
            print("Chức năng xử lý EPUB sẽ được triển khai.")
        else:
            print(f"Định dạng file '{file_extension}' không được hỗ trợ.")