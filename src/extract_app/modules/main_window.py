# file-path: src/extract_app/modules/main_window.py (HOÀN CHỈNH)
# version: 7.1
# last-updated: 2025-09-21
# description: Hotfix - Thêm màn hình loading chuyên dụng thay cho màn hình chào.

import customtkinter as ctk
from customtkinter import filedialog
import sv_ttk
from pathlib import Path
from PIL import Image
import io
import os
import threading
import queue
import subprocess
import tkinter.messagebox as messagebox
import time

from ..core import pdf_parser, epub_parser, storage_handler

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ExtractPDF-EPUB App")
        self.geometry("1000x800")
        sv_ttk.set_theme("light")

        # Khai báo các biến trạng thái
        self.current_results = {}
        self.current_filepath = ""
        self.recent_save_paths = []
        self.results_queue = queue.Queue()

        self._create_main_layout()
        self._create_header()
        self._create_welcome_screen()
        self._create_loading_screen() # Thêm hàm tạo màn hình loading
        self._create_results_view()
        self._create_log_panel()
        
        self.show_welcome_screen()

    def _create_main_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0, minsize=120)

    def _create_header(self):
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        self.select_button = ctk.CTkButton(self.header_frame, text="Chọn Ebook...", command=self._on_select_file_button_click)
        self.select_button.grid(row=0, column=0, padx=10, pady=10)

        save_path_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        save_path_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        save_path_frame.grid_columnconfigure(1, weight=1)
        
        save_label = ctk.CTkLabel(save_path_frame, text="Lưu vào:")
        save_label.grid(row=0, column=0, padx=(0, 5))
        
        self.save_path_combobox = ctk.CTkComboBox(save_path_frame, values=self.recent_save_paths)
        self.save_path_combobox.grid(row=0, column=1, sticky="ew")
        self._setup_default_save_path()

        self.save_button = ctk.CTkButton(self.header_frame, text="Lưu kết quả", command=self._on_save_button_click, state="disabled")
        self.save_button.grid(row=0, column=2, padx=10, pady=10)

    def _create_welcome_screen(self):
        self.welcome_frame = ctk.CTkFrame(self, fg_color="transparent")
        welcome_label = ctk.CTkLabel(self.welcome_frame, text="Vui lòng chọn một file Ebook để bắt đầu", font=("", 24))
        welcome_label.pack(expand=True)

    def _create_loading_screen(self):
        """Tạo frame cho màn hình loading."""
        self.loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.loading_label = ctk.CTkLabel(self.loading_frame, text="Đang xử lý...", font=("", 24))
        self.loading_label.pack(expand=True)

    def _create_results_view(self):
        self.results_frame_main = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame_main.grid_columnconfigure(1, weight=1)
        self.results_frame_main.grid_rowconfigure(0, weight=1)

        self.metadata_panel = ctk.CTkFrame(self.results_frame_main, width=300)
        self.metadata_panel.grid(row=0, column=0, padx=(10, 5), pady=(0, 10), sticky="ns")
        self.metadata_panel.grid_propagate(False)
        self.metadata_panel.grid_rowconfigure(0, weight=0)
        self.metadata_panel.grid_rowconfigure(1, weight=0)
        self.metadata_panel.grid_rowconfigure(2, weight=1)

        self.cover_label = ctk.CTkLabel(self.metadata_panel, text="")
        self.cover_label.grid(row=0, column=0, padx=10, pady=10)
        self.title_label = ctk.CTkLabel(self.metadata_panel, text="Title", font=("", 16, "bold"), wraplength=280)
        self.title_label.grid(row=1, column=0, padx=10, pady=5)
        self.author_label = ctk.CTkLabel(self.metadata_panel, text="Author", wraplength=280)
        self.author_label.grid(row=2, column=0, padx=10, pady=5, sticky="n")

        self.content_panel = ctk.CTkScrollableFrame(self.results_frame_main)
        self.content_panel.grid(row=0, column=1, padx=(5, 10), pady=(0, 10), sticky="nsew")

    def _create_log_panel(self):
        self.log_textbox = ctk.CTkTextbox(self, height=120, wrap="word", state="disabled")
        self.log_textbox.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")

    def _log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", formatted_message)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.update_idletasks()

    def show_welcome_screen(self):
        self.loading_frame.grid_forget()
        self.results_frame_main.grid_forget()
        self.welcome_frame.grid(row=1, column=0, sticky="nsew")

    def show_loading_screen(self, filename):
        """Hiển thị màn hình loading với tên file."""
        self.welcome_frame.grid_forget()
        self.results_frame_main.grid_forget()
        self.loading_label.configure(text=f"Đang phân tích file:\n{filename}...")
        self.loading_frame.grid(row=1, column=0, sticky="nsew")
        self.update_idletasks()
    
    def show_results_view(self):
        self.loading_frame.grid_forget()
        self.welcome_frame.grid_forget()
        self.results_frame_main.grid(row=1, column=0, sticky="nsew")
        
        meta = self.current_results.get('metadata', {})
        self.title_label.configure(text=meta.get('title', 'Không có tiêu đề'))
        self.author_label.configure(text=meta.get('author', 'Không rõ tác giả'))
        
        cover_path = meta.get('cover_image_path', '')
        if cover_path and Path(cover_path).exists():
            try:
                cover_image = Image.open(cover_path)
                cover_image.thumbnail((280, 280 * (cover_image.height / cover_image.width)))
                ctk_cover = ctk.CTkImage(light_image=cover_image, size=cover_image.size)
                self.cover_label.configure(image=ctk_cover, text="")
                self.cover_label.image = ctk_cover 
            except Exception as e:
                self._log(f"Lỗi khi load ảnh bìa: {e}")
                self.cover_label.configure(image=None, text="[Lỗi ảnh bìa]")
                self.cover_label.image = None
        else:
            self.cover_label.configure(image=None, text="[Không có ảnh bìa]")
            self.cover_label.image = None

        self._display_featherweight_content()

    def _clear_results_frame(self):
        for widget in self.content_panel.winfo_children():
            widget.destroy()

    def _display_featherweight_content(self):
        self._clear_results_frame()
        content_list = self.current_results.get('content', [])
        for section_data in content_list:
            title = section_data.get('title', 'Không có tiêu đề')
            content = section_data.get('content', [])
            separator = ctk.CTkLabel(self.content_panel, text=f"--- {title} ---", text_color="gray", font=("", 14, "bold"))
            separator.pack(fill="x", pady=(20, 10), padx=10)
            total_words = 0
            image_count = 0
            for content_type, data in content:
                if content_type == 'text': total_words += len(data.split())
                elif content_type == 'image': image_count += 1
            summary_text = f"[Nội dung chương ({total_words} từ, {image_count} hình ảnh)]"
            summary_label = ctk.CTkLabel(self.content_panel, text=summary_text, anchor="w", justify="left")
            summary_label.pack(fill="x", padx=10, pady=5)

    def _on_select_file_button_click(self):
        filepath = filedialog.askopenfilename(title="Chọn một file Ebook", filetypes=[("Ebooks", "*.pdf *.epub")])
        if not filepath: return
        
        filename = Path(filepath).name
        self._log(f"Đã chọn file: {filename}")
        self._log("Bắt đầu quá trình phân tích. Vui lòng chờ...")

        self.current_filepath = filepath
        self.select_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        
        self.show_loading_screen(filename)
        
        self.progress_bar = ctk.CTkProgressBar(self, mode='indeterminate')
        self.progress_bar.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.start()

        self.worker_thread = threading.Thread(
            target=self._worker_parse_file,
            args=(filepath, self.results_queue)
        )
        self.worker_thread.start()
        self.after(100, self._check_results_queue)

    def _worker_parse_file(self, filepath, q):
        file_extension = Path(filepath).suffix.lower()
        results = {}
        if file_extension == ".pdf":
            results = pdf_parser.parse_pdf(filepath)
        elif file_extension == ".epub":
            results = epub_parser.parse_epub(filepath)
        q.put(results)

    def _check_results_queue(self):
        try:
            results = self.results_queue.get_nowait()
            self.progress_bar.stop()
            self.progress_bar.grid_forget()
            
            self.current_results = results
            if self.current_results and self.current_results.get('content'):
                self._log("Phân tích hoàn tất. Đang hiển thị kết quả...")
                self.show_results_view()
                self.save_button.configure(state="normal")
                self._log("Sẵn sàng.")
            else:
                self._log(f"Lỗi: Không thể trích xuất nội dung từ file {Path(self.current_filepath).name}.")
            
            self.select_button.configure(state="normal")
        except queue.Empty:
            self.after(100, self._check_results_queue)
    
    def _on_save_button_click(self):
        target_dir = self.save_path_combobox.get()
        if not target_dir or not Path(target_dir).is_dir():
            messagebox.showerror("Lỗi Đường Dẫn", f"Đường dẫn không hợp lệ hoặc không tồn tại:\n{target_dir}")
            return
        
        self._log(f"Bắt đầu lưu vào thư mục: {target_dir}...")
        self.save_button.configure(state="disabled")
        self.select_button.configure(state="disabled")

        success, message = storage_handler.save_as_folders(
            self.current_results.get('content', []), Path(target_dir), Path(self.current_filepath).name
        )
        
        self.save_button.configure(state="normal")
        self.select_button.configure(state="normal")

        if success:
            self._log(f"Lưu thành công vào: {message}")
            user_choice = messagebox.askyesno(
                "Lưu Thành Công!",
                f"Đã lưu thành công vào thư mục:\n{message}\n\nBạn có muốn mở thư mục này không?"
            )
            if user_choice:
                try:
                    if os.name == 'nt': # For Windows
                        os.startfile(os.path.realpath(message))
                    elif os.name == 'posix': # For macOS, Linux
                        subprocess.run(['open', os.path.realpath(message)])
                except Exception as e:
                    self._log(f"Lỗi không thể mở thư mục: {e}")
                    messagebox.showerror("Lỗi", f"Không thể mở thư mục:\n{e}")
        else:
            self._log(f"Lưu thất bại: {message}")
            messagebox.showerror("Lưu Thất Bại", f"Đã xảy ra lỗi:\n{message}")
    
    def _setup_default_save_path(self):
        default_path = Path.cwd() / "Output"
        default_path.mkdir(exist_ok=True)
        self.recent_save_paths.append(str(default_path))
        self.save_path_combobox.set(str(default_path))
        self.save_path_combobox.configure(values=self.recent_save_paths)