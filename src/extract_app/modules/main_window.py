# file-path: src/extract_app/modules/main_window.py
# version: 13.0 (Refactored UI)
# last-updated: 2026-01-20
# description: Split UI components into HeaderFrame and ResultsView.

"""
Main window module for the ExtractPDF-EPUB application.

Handles the entire user interface, event handling, and thread management for
parsing and saving ebook content.
"""
# --- Standard Library Imports ---
import os
import queue
import subprocess
import threading
import time
import tkinter.messagebox as messagebox
from pathlib import Path
from typing import Any, Dict, List

# --- Third-Party Imports ---
import customtkinter as ctk
import sv_ttk
from customtkinter import filedialog

# --- Local Application Imports ---
from ..core import content_structurer, epub_parser, pdf_parser, storage_handler
from .ui.header_frame import HeaderFrame
from .ui.results_view import ResultsView

class MainWindow(ctk.CTk):
    """
    Main application window, orchestrating the UI and core logic.
    """

    def __init__(self):
        super().__init__()
        self.title("ExtractPDF-EPUB App")
        self.geometry("1000x800")
        sv_ttk.set_theme("light")

        # Instance Attributes
        self.current_results: Dict[str, Any] = {}
        self.current_filepath: str = ""
        self.recent_save_paths: List[str] = []
        self.results_queue = queue.Queue()
        self.progress_bar: ctk.CTkProgressBar | None = None
        
        # UI Components
        self.header_frame: HeaderFrame
        self.results_view: ResultsView
        self.welcome_frame: ctk.CTkFrame
        self.loading_frame: ctk.CTkFrame
        self.loading_label: ctk.CTkLabel
        self.log_textbox: ctk.CTkTextbox

        # UI Initialization
        self._create_main_layout()
        self._create_header()
        self._create_welcome_screen()
        self._create_loading_screen()
        self._create_results_view()
        self._create_log_panel()
        self.show_welcome_screen()

    def _create_main_layout(self):
        """Configure the main grid layout of the window."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=0, minsize=120)

    def _create_header(self):
        """Create the top header frame."""
        self.header_frame = HeaderFrame(
            self,
            on_select_callback=self._on_select_file_button_click,
            on_save_callback=self._on_save_button_click,
            recent_save_paths=self.recent_save_paths
        )
        self.header_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

    def _create_welcome_screen(self):
        """Create the initial welcome screen."""
        self.welcome_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkLabel(
            self.welcome_frame, text="Vui lòng chọn một file Ebook để bắt đầu", font=("", 24)
        ).pack(expand=True)

    def _create_loading_screen(self):
        """Create the loading animation screen."""
        self.loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.loading_label = ctk.CTkLabel(self.loading_frame, text="Đang xử lý...", font=("", 24))
        self.loading_label.pack(expand=True)

    def _create_results_view(self):
        """Create the results view component."""
        self.results_view = ResultsView(self, log_callback=self._log)
        # Initially hidden

    def _create_log_panel(self):
        """Create the bottom panel for logging messages."""
        self.log_textbox = ctk.CTkTextbox(self, height=120, wrap="word", state="disabled")
        self.log_textbox.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")

    def _log(self, message: str):
        """Append a timestamped message to the log panel."""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", formatted_message)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.update_idletasks()

    def show_welcome_screen(self):
        """Display the welcome screen and hide others."""
        self.loading_frame.grid_forget()
        if hasattr(self, 'results_view'):
            self.results_view.grid_forget()
        self.welcome_frame.grid(row=1, column=0, sticky="nsew")

    def show_loading_screen(self, filename: str):
        """Display the loading screen with the current filename."""
        self.welcome_frame.grid_forget()
        if hasattr(self, 'results_view'):
            self.results_view.grid_forget()
        self.loading_label.configure(text=f"Đang phân tích file:\n{filename}...")
        self.loading_frame.grid(row=1, column=0, sticky="nsew")
        self.update_idletasks()

    def show_results_view(self):
        """Display the results view and populate it with data."""
        self.loading_frame.grid_forget()
        self.welcome_frame.grid_forget()
        self.results_view.grid(row=1, column=0, sticky="nsew")
        
        # Populate results
        self.results_view.show_results(self.current_results)
        self.header_frame.set_save_button_state("normal")

    def _on_select_file_button_click(self):
        """Handle the 'Select Ebook' button click event."""
        filepath = filedialog.askopenfilename(
            title="Chọn một file Ebook", filetypes=[("Ebooks", "*.pdf *.epub")]
        )
        if not filepath:
            return

        filename = Path(filepath).name
        self._log(f"Đã chọn file: {filename}")
        self._log("Bắt đầu quá trình phân tích...")

        self.current_filepath = filepath
        self.header_frame.set_buttons_state("disabled")
        self.show_loading_screen(filename)

        self.progress_bar = ctk.CTkProgressBar(self, mode='indeterminate')
        self.progress_bar.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.start()

        threading.Thread(
            target=self._worker_parse_file, args=(filepath, self.results_queue), daemon=True
        ).start()
        self.after(100, self._check_results_queue)

    def _worker_parse_file(self, filepath, q):
        """
        Worker thread function to parse the ebook file off the main UI thread.
        """
        file_extension = Path(filepath).suffix.lower()
        results = {}
        try:
            if file_extension == ".pdf":
                raw_results = pdf_parser.parse_pdf(filepath)
                final_tree = []
                for chapter_node in raw_results.get('content', []):
                    # Basic restructuring if needed
                    articles = content_structurer.structure_pdf_articles(
                        chapter_node.get('content', [])
                    )
                    children_nodes = [
                        {'title': article.get('subtitle', 'Nội dung'),
                         'content': article.get('content', []),
                         'children': []}
                        for article in articles if article.get('subtitle') or article.get('content')
                    ]
                    chapter_node['children'] = children_nodes
                    chapter_node['content'] = []
                    final_tree.append(chapter_node)
                raw_results['content'] = final_tree
                results = raw_results
            elif file_extension == ".epub":
                results = epub_parser.parse_epub(filepath)
        except Exception as e:
            results = {'content': [], 'metadata': {}, 'error': str(e)}
            
        q.put(results)

    def _check_results_queue(self):
        """Periodically check the queue for results from the worker thread."""
        try:
            results = self.results_queue.get_nowait()
            if self.progress_bar:
                self.progress_bar.stop()
                self.progress_bar.grid_forget()

            self.current_results = results
            
            # Check for error in results or explicit error key
            if results.get('error'):
                 self._log(f"Lỗi: {results.get('error')}")
            
            if self.current_results and self.current_results.get('content'):
                self._log("Phân tích hoàn tất.")
                self.show_results_view()
            else:
                error_content = "Không tìm thấy nội dung hợp lệ."
                if not results.get('error'):
                     self._log(f"Cảnh báo: {error_content}")
                self.header_frame.set_select_button_state("normal")
                
        except queue.Empty:
            self.after(100, self._check_results_queue)

    def _on_save_button_click(self):
        """Handle the save button click event."""
        target_dir = self.header_frame.get_save_path()
        if not target_dir or not Path(target_dir).is_dir():
            messagebox.showerror("Lỗi Đường Dẫn", f"Đường dẫn không hợp lệ: {target_dir}")
            return
        self._log(f"Bắt đầu lưu vào thư mục: {target_dir}...")
        self.header_frame.set_buttons_state("disabled")

        success, message = storage_handler.save_as_folders(
            self.current_results.get('content', []),
            Path(target_dir),
            Path(self.current_filepath).name
        )

        self.header_frame.set_buttons_state("normal")
        if success:
            self._log(f"Lưu thành công vào: {message}")
            if messagebox.askyesno(
                "Lưu Thành Công!",
                f"Đã lưu thành công vào:\n{message}\n\nBạn có muốn mở thư mục này không?"
            ):
                self._open_folder(message)
        else:
            self._log(f"Lưu thất bại: {message}")

    def _open_folder(self, path: str):
        """Open the specified folder in the default file explorer."""
        try:
            if os.name == 'nt':  # For Windows
                os.startfile(os.path.realpath(path))
            elif os.name == 'posix':  # For macOS, Linux
                subprocess.run(['open', os.path.realpath(path)], check=True)
        except AttributeError:
             # Fallback for environments like Linux without os.startfile
            if os.name == 'posix':
                 subprocess.run(['xdg-open', os.path.realpath(path)], check=True)
            else:
                 self._log("Lỗi: Không thể tự động mở thư mục trên hệ điều hành này.")
        except (OSError, subprocess.CalledProcessError) as e:
            self._log(f"Lỗi không thể mở thư mục: {e}")