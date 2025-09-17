# file-path: src/extract_app/modules/main_window.py
# version: 2.4
# last-updated: 2025-09-17
# description: Cập nhật để xử lý và hiển thị dữ liệu có cấu trúc (text/image).

import customtkinter as ctk
from customtkinter import filedialog
import sv_ttk
from pathlib import Path

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

        self.results_textbox = ctk.CTkTextbox(self, wrap="word")
        self.results_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def _on_select_file_button_click(self):
        file_types = [("Ebook files", "*.pdf *.epub"), ("All files", "*.*")]
        filepath = filedialog.askopenfilename(title="Chọn một file Ebook", filetypes=file_types)
        
        if not filepath:
            print("Không có file nào được chọn.")
            return

        self.selected_file_label.configure(text=filepath)
        print(f"File đã chọn: {filepath}")
        
        self.results_textbox.delete("1.0", "end")

        file_extension = Path(filepath).suffix.lower()
        if file_extension == ".pdf":
            print("\n--- Bắt đầu trích xuất PDF ---")
            content_list = pdf_parser.parse_pdf(filepath)
            
            image_count = 0
            full_text = []
            for content_type, data in content_list:
                if content_type == 'text':
                    full_text.append(data)
                elif content_type == 'image':
                    image_count += 1
                    print(f"Đã tìm thấy 1 ảnh, kích thước {len(data)} bytes.")
            
            self.results_textbox.insert("1.0", "".join(full_text))
            print(f"Tổng cộng: {image_count} ảnh được tìm thấy.")
            print("--- Hoàn tất trích xuất PDF ---\n")
            
        elif file_extension == ".epub":
            # ... xử lý EPUB
            pass
        else:
            # ... xử lý file không hỗ trợ
            pass