# file-path: src/extract_app/modules/main_window.py
# version: 4.3
# last-updated: 2025-09-19
# description: Sửa lỗi NameError do thiếu import filedialog cho nút Chọn File.

import customtkinter as ctk
from customtkinter import filedialog # Thêm lại import này cho nút "Chọn File"
import sv_ttk
from pathlib import Path
from PIL import Image
import io
from ..core import pdf_parser, epub_parser, storage_handler

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ExtractPDF-EPUB App - Verification Tool")
        self.geometry("800x650")
        sv_ttk.set_theme("light")
        self.current_content = []
        self.current_filepath = ""
        self._create_widgets()

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # KHUNG CHỌN FILE
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        control_frame.grid_columnconfigure(1, weight=1)
        select_button = ctk.CTkButton(control_frame, text="Chọn File Ebook...", command=self._on_select_file_button_click)
        select_button.grid(row=0, column=0, padx=10, pady=10)
        self.selected_file_label = ctk.CTkLabel(control_frame, text="Chưa có file nào được chọn.", anchor="w")
        self.selected_file_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # KHUNG LƯU FILE
        save_frame = ctk.CTkFrame(self)
        save_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        save_frame.grid_columnconfigure(1, weight=1)
        save_label = ctk.CTkLabel(save_frame, text="Dán đường dẫn thư mục để lưu:")
        save_label.grid(row=0, column=0, padx=10, pady=10)
        self.save_path_entry = ctk.CTkEntry(save_frame, placeholder_text="Ví dụ: D:\\Ebooks\\Output")
        self.save_path_entry.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="ew")
        self.save_button = ctk.CTkButton(save_frame, text="Lưu kết quả", command=self._on_save_button_click, state="disabled")
        self.save_button.grid(row=0, column=2, padx=10, pady=10)
        
        # KHUNG KẾT QUẢ
        self.results_frame = ctk.CTkScrollableFrame(self)
        self.results_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
    
    def _on_select_file_button_click(self):
        # Hàm này sử dụng filedialog.askopenfilename, nên cần import ở trên
        filepath = filedialog.askopenfilename(title="Chọn một file Ebook", filetypes=[("Ebook files", "*.pdf *.epub")])
        if not filepath: return
        
        self.current_filepath = filepath
        self.selected_file_label.configure(text=filepath)
        self._clear_results_frame()
        self.save_button.configure(state="disabled")
        self.current_content = []

        file_extension = Path(filepath).suffix.lower()
        if file_extension == ".pdf":
            self.current_content = pdf_parser.parse_pdf(filepath)
        elif file_extension == ".epub":
            self.current_content = epub_parser.parse_epub(filepath)
        
        if self.current_content:
            self.after(100, lambda: self._display_results(self.current_content))
            self.save_button.configure(state="normal")
    
    def _on_save_button_click(self):
        if not self.current_content or not self.current_filepath:
            print("Không có nội dung để lưu.")
            return
        
        target_dir = self.save_path_entry.get()
        
        if not target_dir or not Path(target_dir).is_dir():
            print(f"Lỗi: Đường dẫn không hợp lệ hoặc không tồn tại: {target_dir}")
            return
        
        print(f"Bắt đầu lưu vào thư mục: {target_dir}")
        success, message = storage_handler.save_as_folders(
            self.current_content, 
            Path(target_dir), 
            Path(self.current_filepath).name
        )
        
        if success:
            print(f"Lưu thành công, dữ liệu được lưu tại: {message}")
        else:
            print(f"Lưu thất bại: {message}")

    def _clear_results_frame(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

    def _display_results(self, structured_content):
        # ... (hàm này không đổi)
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
                    anchor_text = f"[IMAGE ANCHOR]: {data}"
                    anchor_label = ctk.CTkLabel(self.results_frame, text=anchor_text, text_color="blue", anchor="w")
                    anchor_label.grid(sticky="w", pady=5, padx=5)