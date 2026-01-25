# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/main_window.py
# Version: 1.1.0
# Author: Antigravity
# Description: Main window module orchestrating UI and core logic.
# --------------------------------------------------------------------------------

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
from .ui.sidebar import SidebarFrame
from .ui.top_bar import TopBarFrame
from .ui.dashboard_view import DashboardView
from .ui.results_view import ResultsView
# Note: HeaderFrame is no longer used in the new layout

class MainWindow(ctk.CTk):
    """
    Main application window, orchestrating the UI and core logic.
    """

    def __init__(self):
        super().__init__()
        self.title("ExtractPDF-EPUB App - Modern UI")
        self.geometry("1100x800")
        # Theme Configuration
        ctk.set_appearance_mode("Dark")
        sv_ttk.set_theme("dark") 

        # Instance Attributes
        self.current_results: Dict[str, Any] = {}
        self.current_filepath: str = ""
        self.recent_save_paths: List[str] = []
        self.results_queue = queue.Queue()
        self.progress_bar: ctk.CTkProgressBar | None = None
        
        # UI Components
        self.sidebar: SidebarFrame
        self.top_bar: TopBarFrame
        self.dashboard_view: DashboardView
        self.results_view: ResultsView
        self.loading_frame: ctk.CTkFrame
        self.loading_label: ctk.CTkLabel
        
        # Container for swappable views
        self.content_area: ctk.CTkFrame

        # UI Initialization
        self._create_main_layout()
        self._init_components()
        self._show_view("dashboard")

    def _create_main_layout(self):
        """Configure the main grid layout: Sidebar (Left) + Content (Right)."""
        self.grid_columnconfigure(0, weight=0, minsize=200) # Sidebar
        self.grid_columnconfigure(1, weight=1)              # Content
        self.grid_rowconfigure(0, weight=1)

    def _init_components(self):
        """Initialize all UI components."""
        # 1. Sidebar
        # 1. Sidebar
        self.sidebar = SidebarFrame(
            self, 
            on_navigate=self._on_navigate,
            on_close_book=self._close_current_file
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 2. Right Side Container (Top Bar + View Area)
        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.grid(row=0, column=1, sticky="nsew")
        self.right_container.grid_rowconfigure(1, weight=1)
        self.right_container.grid_columnconfigure(0, weight=1)
        
        # 3. Top Bar
        self.top_bar = TopBarFrame(self.right_container, on_close=self._close_current_file)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        
        # 4. Content Area (Holds Dashboard, Loading, Results)
        self.content_area = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # 5. Views
        self.dashboard_view = DashboardView(self.content_area, on_import=self._on_select_file)
        self.results_view = ResultsView(self.content_area, on_extract=self._on_extract_content)
        
        # Loading Screen
        self.loading_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.loading_label = ctk.CTkLabel(self.loading_frame, text="Đang xử lý...", font=("", 24))
        self.loading_label.pack(expand=True)

    def _on_navigate(self, view_name: str):
        """Handle sidebar navigation events."""
        self.sidebar.set_active_button(view_name)
        
        if view_name == "dashboard":
            # Smart Navigation: If we have results, show them. Else show import screen.
            if self.current_results and self.current_results.get('content'):
                self._show_view("results")
            elif self.current_results and self.current_results.get('error'):
                 # If there was an error, maybe show dashboard to try again
                 self._show_view("dashboard")
            else:
                 # Check if we are currently loading
                 if self.loading_frame.winfo_viewable():
                     self._show_view("loading")
                 else:
                     self._show_view("dashboard")

        elif view_name == "library":
            messagebox.showinfo("Thông báo", "Tính năng Thư viện đang được phát triển.\nSẽ có trong phiên bản tới!")
        elif view_name == "settings":
            messagebox.showinfo("Thông báo", "Tính năng Cài đặt đang được phát triển.\nSẽ có trong phiên bản tới!")

    def _show_view(self, view_name: str):
        """Switch the visible view in the content area."""
        # Hide all
        self.dashboard_view.grid_forget()
        self.results_view.grid_forget()
        self.loading_frame.grid_forget()
        
        # Show selected
        if view_name == "dashboard":
            self.dashboard_view.grid(row=0, column=0, sticky="nsew")
        elif view_name == "results":
            self.results_view.grid(row=0, column=0, sticky="nsew")
        elif view_name == "loading":
            self.loading_frame.grid(row=0, column=0, sticky="nsew")

    def _on_select_file(self):
        """Handle file selection from Dashboard."""
        filepath = filedialog.askopenfilename(
            title="Chọn một file Ebook", filetypes=[("Ebooks", "*.pdf *.epub")]
        )
        if not filepath:
            return

        filename = Path(filepath).name
        self.current_filepath = filepath
        self.top_bar.set_file_path(filepath)
        
        # Switch to loading
        self._show_view("loading")
        self.loading_label.configure(text=f"Đang phân tích file:\n{filename}...")

        # Start parsing
        self.progress_bar = ctk.CTkProgressBar(self.loading_frame, mode='indeterminate')
        self.progress_bar.pack(pady=20)
        self.progress_bar.start()

        threading.Thread(
            target=self._worker_parse_file, args=(filepath, self.results_queue), daemon=True
        ).start()
        self.after(100, self._check_results_queue)

    def _worker_parse_file(self, filepath, q):
        """Worker thread function."""
        # Reuse existing parsing logic
        file_extension = Path(filepath).suffix.lower()
        results = {}
        try:
            if file_extension == ".pdf":
                raw_results = pdf_parser.parse_pdf(filepath)
                # ... same restructuring logic as before ...
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
        except Exception as e:
            results = {'content': [], 'metadata': {}, 'error': str(e)}
            
        q.put(results)

    def _check_results_queue(self):
        """Check for parsing results."""
        try:
            results = self.results_queue.get_nowait()
            if self.progress_bar:
                self.progress_bar.stop()
            
            self.current_results = results
            
            if results.get('error'):
                 messagebox.showerror("Lỗi", f"Lỗi phân tích: {results.get('error')}")
                 self._show_view("dashboard")
                 return
            
            if self.current_results and self.current_results.get('content'):
                self._show_view("results")
                self.results_view.show_results(self.current_results)
                
                # Update Sidebar State
                self.sidebar.show_active_book_controls()
                self.sidebar.set_active_button("results")
                
                # IMPORTANT: We need to enable the 'Extract' button in ResultsView here
                # accessing: self.results_view.set_extract_enabled(True) (To be implemented)
            else:
                 messagebox.showwarning("Cảnh báo", "Không tìm thấy nội dung hợp lệ.")
                 self._show_view("dashboard")
                
        except queue.Empty:
            self.after(100, self._check_results_queue)

    # Note: _on_save_button_click logic removed from here as it will move to ResultsView
    # or be coordinated from here if ResultsView emits an event.
    def _on_extract_content(self, target_dir: str):
        """Handle extraction trigger from ResultsView."""
        if not target_dir:
            return

        # Check for overwrite
        output_name = Path(self.current_filepath).name
        full_output_path = Path(target_dir) / output_name.replace(" ", "_").replace(".epub", "").replace(".pdf", "")
        
        if full_output_path.exists():
            if not messagebox.askyesno(
                "Thư mục đã tồn tại", 
                f"Thư mục '{full_output_path.name}' đã tồn tại.\nBạn có muốn ghi đè (xóa và tạo lại) không?"
            ):
                return
        
        # Execute save
        success, message = storage_handler.save_as_folders(
            self.current_results.get('content', []),
            Path(target_dir),
            Path(self.current_filepath).name
        )

        if success:
             if messagebox.askyesno(
                "Trích xuất thành công",
                f"Đã lưu vào:\n{message}\nMở thư mục ngay?"
            ):
                self._open_folder(message)
        else:
            messagebox.showerror("Lỗi trích xuất", f"Có lỗi xảy ra: {message}")

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
                 pass # Cannot handle open folder
        except (OSError, subprocess.CalledProcessError):
             pass # Simple ignore if fails

    def _close_current_file(self) -> None:
        """
        Clear current result and return to dashboard.
        
        Prompts the user for confirmation before closing.
        """
        if self.current_results:
            if messagebox.askyesno("Đóng file", "Bạn có chắc muốn đóng file hiện tại không?"):
                 self.current_results = {}
                 self.current_filepath = ""
                 self.top_bar.set_file_path("")
                 
                 # Update Widgets
                 self.sidebar.hide_active_book_controls()
                 self._show_view("dashboard")
                 self.sidebar.set_active_button("dashboard")