# file-path: src/extract_app/modules/main_window.py
# version: 11.1 (Pylint Compliance)
# last-updated: 2025-09-26
# description: Fixes Pylint errors, including a platform-specific crash, and adds full documentation.

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
from typing import List, Dict, Any

# --- Third-Party Imports ---
import customtkinter as ctk
import sv_ttk
from PIL import Image
from customtkinter import filedialog

# --- Local Application Imports ---
from ..core import content_structurer, epub_parser, pdf_parser, storage_handler


class MainWindow(ctk.CTk):
    """
    Main application window, orchestrating the UI and core logic.

    Attributes:
        current_results (dict): Stores the structured data from the last parsed file.
        current_filepath (str): The path to the currently loaded ebook file.
        recent_save_paths (list): A list of recently used directories for saving results.
        results_queue (queue.Queue): A queue to safely pass results from the worker thread to the main UI thread.
        progress_bar (ctk.CTkProgressBar): The progress bar widget shown during parsing.
    """
    # pylint: disable=too-many-instance-attributes

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
        """Create the top header frame with file selection and save controls."""
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.select_button = ctk.CTkButton(
            self.header_frame, text="Chọn Ebook...", command=self._on_select_file_button_click
        )
        self.select_button.grid(row=0, column=0, padx=10, pady=10)

        save_path_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        save_path_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        save_path_frame.grid_columnconfigure(1, weight=1)

        save_label = ctk.CTkLabel(save_path_frame, text="Lưu vào:")
        save_label.grid(row=0, column=0, padx=(0, 5))

        self.save_path_combobox = ctk.CTkComboBox(save_path_frame, values=self.recent_save_paths)
        self.save_path_combobox.grid(row=0, column=1, sticky="ew")
        self._setup_default_save_path()

        self.save_button = ctk.CTkButton(
            self.header_frame, text="Lưu kết quả", command=self._on_save_button_click, state="disabled"
        )
        self.save_button.grid(row=0, column=2, padx=10, pady=10)

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
        """Create the main view for displaying parsed results."""
        self.results_frame_main = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame_main.grid_columnconfigure(1, weight=1)
        self.results_frame_main.grid_rowconfigure(0, weight=1)

        self.metadata_panel = ctk.CTkFrame(self.results_frame_main, width=300)
        self.metadata_panel.grid(row=0, column=0, padx=(10, 5), pady=(0, 10), sticky="ns")
        self.metadata_panel.grid_propagate(False)
        self.metadata_panel.grid_rowconfigure(2, weight=1)

        self.cover_label = ctk.CTkLabel(self.metadata_panel, text="")
        self.cover_label.grid(row=0, column=0, padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            self.metadata_panel, text="Title", font=("", 16, "bold"), wraplength=280
        )
        self.title_label.grid(row=1, column=0, padx=10, pady=5)

        self.author_label = ctk.CTkLabel(self.metadata_panel, text="Author", wraplength=280)
        self.author_label.grid(row=2, column=0, padx=10, pady=5, sticky="n")

        self.content_panel = ctk.CTkScrollableFrame(self.results_frame_main)
        self.content_panel.grid(row=0, column=1, padx=(5, 10), pady=(0, 10), sticky="nsew")

    def _create_log_panel(self):
        """Create the bottom panel for logging messages."""
        self.log_textbox = ctk.CTkTextbox(self, height=120, wrap="word", state="disabled")
        self.log_textbox.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")

    def _log(self, message):
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
        self.results_frame_main.grid_forget()
        self.welcome_frame.grid(row=1, column=0, sticky="nsew")

    def show_loading_screen(self, filename):
        """Display the loading screen with the current filename."""
        self.welcome_frame.grid_forget()
        self.results_frame_main.grid_forget()
        self.loading_label.configure(text=f"Đang phân tích file:\n{filename}...")
        self.loading_frame.grid(row=1, column=0, sticky="nsew")
        self.update_idletasks()

    def show_results_view(self):
        """Display the results view and populate it with data."""
        self.loading_frame.grid_forget()
        self.welcome_frame.grid_forget()
        self.results_frame_main.grid(row=1, column=0, sticky="nsew")

        meta = self.current_results.get('metadata', {})
        self.title_label.configure(text=meta.get('title', 'Không có tiêu đề'))
        self.author_label.configure(text=meta.get('author', 'Không rõ tác giả'))

        cover_path = meta.get('cover_image_path', '')
        if cover_path and Path(cover_path).exists():
            try:
                img = Image.open(cover_path)
                img.thumbnail((280, 280))
                ctk_img = ctk.CTkImage(light_image=img, size=img.size)
                self.cover_label.configure(image=ctk_img, text="")
                self.cover_label.image = ctk_img
            except Exception as e:
                self._log(f"Lỗi khi load ảnh bìa: {e}")
                self.cover_label.configure(image=None, text="[Lỗi ảnh bìa]")
        else:
            self.cover_label.configure(image=None, text="[Không có ảnh bìa]")

        self._display_content_tree()

    def _clear_content_panel(self):
        """Remove all widgets from the content display panel."""
        for widget in self.content_panel.winfo_children():
            widget.destroy()

    def _display_content_tree(self):
        """Recursively build and display the content tree structure."""
        self._clear_content_panel()
        content_tree = self.current_results.get('content', [])
        self._create_tree_view_nodes(self.content_panel, content_tree, level=0)

    def _create_tree_view_nodes(self, parent_widget, nodes: List[Dict[str, Any]], level: int):
        """Create the UI widgets for a list of nodes at a specific indentation level."""
        indent = level * 25
        for node_data in nodes:
            node_title = node_data.get('title', 'No Title')
            children = node_data.get('children', [])
            node_container = ctk.CTkFrame(parent_widget, fg_color="transparent")
            node_container.pack(fill="x", expand=True)
            header_frame = ctk.CTkFrame(node_container, fg_color="transparent")
            header_frame.pack(fill="x", padx=(indent, 0), pady=1)
            header_frame.grid_columnconfigure(1, weight=1)
            children_frame = ctk.CTkFrame(node_container, fg_color="transparent")
            def toggle(button, frame):
                if frame.winfo_viewable():
                    frame.pack_forget(); button.configure(text="+")
                else:
                    frame.pack(fill="x", expand=True, padx=(0,0), pady=(0,0)); button.configure(text="-")
            toggle_button = ctk.CTkButton(header_frame, text="+", width=28, height=28)
            toggle_button.grid(row=0, column=0, sticky="w")
            title_label = ctk.CTkLabel(header_frame, text=node_title, font=("", 14), anchor="w")
            title_label.grid(row=0, column=1, sticky="ew", padx=5)
            summary_label = self._create_summary_label(header_frame, node_data)
            summary_label.grid(row=0, column=2, sticky="e", padx=5)
            if not children:
                toggle_button.configure(state="disabled", fg_color="transparent", text="")
            else:
                toggle_button.configure(command=lambda b=toggle_button, f=children_frame: toggle(b, f))
            if children:
                self._create_tree_view_nodes(children_frame, children, level + 1)

    def _aggregate_content_from_children(self, node: Dict[str, Any]) -> List:
        """Recursively gather all content from a node and its children."""
        aggregated_content = list(node.get('content', []))
        for child in node.get('children', []):
            aggregated_content.extend(self._aggregate_content_from_children(child))
        return aggregated_content

    def _create_summary_label(self, master, node_data: Dict[str, Any]) -> ctk.CTkLabel:
        """Create a summary label showing word and image counts for a node."""
        content_to_summarize = self._aggregate_content_from_children(node_data)
        total_words = sum(
            len(str(data).split()) for c_type, data in content_to_summarize if c_type == 'text'
        )
        image_count = sum(1 for c_type, _ in content_to_summarize if c_type == 'image')
        summary_text = f"[{total_words} từ, {image_count} ảnh]"
        return ctk.CTkLabel(master, text=summary_text, text_color="gray")

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
        self.select_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
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

        if file_extension == ".pdf":
            raw_results = pdf_parser.parse_pdf(filepath)
            final_tree = []
            for chapter_node in raw_results.get('content', []):
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
        q.put(results)

    def _check_results_queue(self):
        """Periodically check the queue for results from the worker thread."""
        try:
            results = self.results_queue.get_nowait()
            if self.progress_bar:
                self.progress_bar.stop()
                self.progress_bar.grid_forget()

            self.current_results = results
            if self.current_results and self.current_results.get('content'):
                self._log("Phân tích hoàn tất.")
                self.show_results_view()
                self.save_button.configure(state="normal")
            else:
                error_content = (self.current_results.get('content') or [{}])[0].get(
                    'content', '[Không có chi tiết]'
                )
                self._log(f"Lỗi: Không thể trích xuất nội dung. Chi tiết: {error_content}")
            self.select_button.configure(state="normal")
        except queue.Empty:
            self.after(100, self._check_results_queue)

    def _on_save_button_click(self):
        """Handle the save button click event."""
        target_dir = self.save_path_combobox.get()
        if not target_dir or not Path(target_dir).is_dir():
            messagebox.showerror("Lỗi Đường Dẫn", f"Đường dẫn không hợp lệ: {target_dir}")
            return
        self._log(f"Bắt đầu lưu vào thư mục: {target_dir}...")
        self.save_button.configure(state="disabled")
        self.select_button.configure(state="disabled")

        success, message = storage_handler.save_as_folders(
            self.current_results.get('content', []),
            Path(target_dir),
            Path(self.current_filepath).name
        )

        self.save_button.configure(state="normal")
        self.select_button.configure(state="normal")
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
            # Fallback for environments where os.startfile is not available (like Linux)
            if os.name == 'posix':
                 subprocess.run(['xdg-open', os.path.realpath(path)], check=True)
            else:
                 self._log("Lỗi: Không thể tự động mở thư mục trên hệ điều hành này.")
        except (OSError, subprocess.CalledProcessError) as e:
            self._log(f"Lỗi không thể mở thư mục: {e}")

    def _setup_default_save_path(self):
        """Create and set the default 'Output' directory for saving results."""
        default_path = Path.cwd() / "Output"
        default_path.mkdir(exist_ok=True)
        self.recent_save_paths.append(str(default_path))
        self.save_path_combobox.set(str(default_path))