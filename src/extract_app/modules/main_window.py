# file-path: src/extract_app/modules/main_window.py
# version: 3.1
# last-updated: 2025-09-17
# description: Tích hợp EPUB parser vào luồng xử lý chính.

import customtkinter as ctk
from customtkinter import filedialog
import sv_ttk
from pathlib import Path
from PIL import Image
import io

from ..core import pdf_parser, epub_parser # Thêm epub_parser

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ExtractPDF-EPUB App")
        self.geometry("800x600")
        sv_ttk.set_theme("light")
        self._create_widgets()

    def _create_widgets(self):
        # ... (không thay đổi)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        select_button = ctk.CTkButton(input_frame, text="Chọn File Ebook...", command=self._on_select_file_button_click)
        select_button.grid(row=0, column=0, padx=10, pady=10)

        self.selected_file_label = ctk.CTkLabel(input_frame, text="Chưa có file nào được chọn.", anchor="w")
        self.selected_file_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.results_frame = ctk.CTkScrollableFrame(self)
        self.results_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)


    def _clear_results_frame(self):
        # ... (không thay đổi)
        for widget in self.results_frame.winfo_children():
            widget.destroy()

    def _display_results(self, content_list):
        # ... (không thay đổi)
        self._clear_results_frame()
        
        frame_width = self.results_frame.winfo_width() - 30 
        if frame_width < 100: frame_width = 600

        for content_type, data in content_list:
            if content_type == 'text':
                text_label = ctk.CTkLabel(
                    self.results_frame, 
                    text=data, 
                    wraplength=frame_width, 
                    justify="left",
                    anchor="w"
                )
                text_label.grid(sticky="w", padx=5, pady=5)
            elif content_type == 'image':
                try:
                    image_data = Image.open(io.BytesIO(data))
                    ctk_image = ctk.CTkImage(light_image=image_data, size=image_data.size)
                    
                    image_label = ctk.CTkLabel(self.results_frame, image=ctk_image, text="")
                    image_label.grid(pady=10)
                except Exception as e:
                    print(f"Lỗi khi hiển thị ảnh: {e}")


    def _on_select_file_button_click(self):
        filepath = filedialog.askopenfilename(title="Chọn một file Ebook", filetypes=[("Ebook files", "*.pdf *.epub")])
        if not filepath: return

        self.selected_file_label.configure(text=filepath)
        self._clear_results_frame()

        content_list = []
        file_extension = Path(filepath).suffix.lower()

        if file_extension == ".pdf":
            print("\n--- Bắt đầu trích xuất PDF ---")
            content_list = pdf_parser.parse_pdf(filepath)
            print("--- Hoàn tất trích xuất PDF ---\n")
        elif file_extension == ".epub":
            print("\n--- Bắt đầu trích xuất EPUB ---")
            content_list = epub_parser.parse_epub(filepath)
            print("--- Hoàn tất trích xuất EPUB ---\n")
        else:
            print(f"Định dạng file '{file_extension}' không được hỗ trợ.")

        if content_list:
            self.after(100, lambda: self._display_results(content_list))