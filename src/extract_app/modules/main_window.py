# file-path: src/extract_app/modules/main_window.py
# version: 3.6
# last-updated: 2025-09-18
# description: Hiển thị anchor (đường dẫn) cho ảnh thay vì load ảnh thật.

import customtkinter as ctk
from customtkinter import filedialog
import sv_ttk
from pathlib import Path
from PIL import Image
import io
from ..core import pdf_parser, epub_parser

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ExtractPDF-EPUB App - Verification Tool") # Đổi tên để rõ vai trò
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
        for widget in self.results_frame.winfo_children():
            widget.destroy()

    def _display_results(self, structured_content):
        self._clear_results_frame()
        frame_width = self.results_frame.winfo_width() - 30 
        if frame_width < 100: frame_width = 600

        for section_data in structured_content:
            title = section_data.get('title', 'Không có tiêu đề')
            content = section_data.get('content', [])

            separator = ctk.CTkLabel(self.results_frame, text=f"--- {title} ---", text_color="gray", font=("", 14, "bold"))
            separator.grid(pady=(20, 10))

            for content_type, data in content:
                if content_type == 'text':
                    text_label = ctk.CTkLabel(self.results_frame, text=data, wraplength=frame_width, justify="left", anchor="w")
                    text_label.grid(sticky="w", padx=5, pady=5)
                elif content_type == 'image':
                    # Logic hiển thị ảnh được CẬP NHẬT
                    # Data bây giờ là đường dẫn (string), chúng ta chỉ hiển thị nó
                    anchor_text = f"[IMAGE ANCHOR]: {data}"
                    
                    # Hiển thị anchor thay vì ảnh thật
                    anchor_label = ctk.CTkLabel(self.results_frame, text=anchor_text, text_color="blue", anchor="w")
                    anchor_label.grid(sticky="w", pady=5, padx=5)
    
    def _on_select_file_button_click(self):
        # ... (logic không đổi)
        filepath = filedialog.askopenfilename(title="Chọn một file Ebook", filetypes=[("Ebook files", "*.pdf *.epub")])
        if not filepath: return
        self.selected_file_label.configure(text=filepath)
        self._clear_results_frame()
        content_list = []
        file_extension = Path(filepath).suffix.lower()
        if file_extension == ".pdf":
            content_list = pdf_parser.parse_pdf(filepath)
        elif file_extension == ".epub":
            pass 
        if content_list:
            self.after(100, lambda: self._display_results(content_list))