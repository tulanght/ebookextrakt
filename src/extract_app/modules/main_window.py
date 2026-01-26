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
from ..core.history_manager import HistoryManager # New Import
from ..shared import debug_logger
from .ui.sidebar import SidebarFrame
from .ui.top_bar import TopBarFrame
from .ui.dashboard_view import DashboardView
from .ui.results_view import ResultsView
from .ui.log_panel import LogPanel
from .ui.loading_overlay import LoadingOverlay

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
        
        # Managers
        self.history_manager = HistoryManager() # Initialize Manager
        
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
        
        # 2. Right Side Container (Top Bar + View Area + Log)
        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.grid(row=0, column=1, sticky="nsew")
        self.right_container.grid_rowconfigure(1, weight=1) # Content Area
        self.right_container.grid_rowconfigure(2, weight=0) # Log Panel
        self.right_container.grid_columnconfigure(0, weight=1)
        
        # 3. Top Bar
        self.top_bar = TopBarFrame(self.right_container, on_close=self._close_current_file)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        
        # 4. Content Area (Holds Dashboard, Results)
        self.content_area = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # 5. Log Panel (Bottom)
        self.log_panel = LogPanel(self.right_container, height=60)
        self.log_panel.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Connect Logger
        # Use lambda or direct method to route messages to the UI panel on the main thread.
        # Since tkinter is not thread-safe for GUI updates from workers, we should technically use queue/after.
        # However, for simple appending, many tk implementations handle it or crash. 
        # Best practice: Wrapper. But for now direct call (assuming writer uses after/event if needed, or risked).
        # We will use .after logic in write_log if crashes occur. 
        # Re-check LogPanel implementation... it uses direct calls. 
        # Let's wrap it in an `after` call to be safe from threads.
        debug_logger.register_listener(lambda msg: self.after(0, self.log_panel.write_log, msg))

        # 6. Views
        self.dashboard_view = DashboardView(self.content_area, on_import=self._on_select_file)
        # Manually inject the open_callback because I cannot change signature easily if generic
        # OR update class init. Wait, I didn't update DashboardView init signature to accept callback.
        # But I added update_history(..., open_callback).
        
        self.results_view = ResultsView(self.content_area, on_extract=self._on_extract_content)
        
        # 7. Loading Overlay (Replaces old loading_frame)
        self.loading_overlay = LoadingOverlay(self.content_area)
        
        # Initial Load of History
        self._update_dashboard_history()

    def _update_dashboard_history(self):
        """Reload history from manager and update dashboard."""
        history = self.history_manager.load_history()
        self.dashboard_view.update_history(history, self._on_open_recent_file)

    def _on_open_recent_file(self, filepath: str):
        """Handle opening a file from history."""
        if not Path(filepath).exists():
            if messagebox.askyesno("File không tồn tại", f"File không tìm thấy:\n{filepath}\nXóa khỏi lịch sử?"):
                self.history_manager.remove_entry(filepath)
                self._update_dashboard_history()
            return
            
        self._start_parsing(filepath)

    def _on_navigate(self, view_name: str):
        """Handle sidebar navigation events."""
        self.sidebar.set_active_button(view_name)
        
        if view_name == "dashboard":
            self._update_dashboard_history() # Refresh when returning to dashboard
            # Smart Navigation: If we have results, show them. Else show import screen.
            if self.current_results and self.current_results.get('content'):
                self._show_view("results")
            elif self.current_results and self.current_results.get('error'):
                 # If there was an error, maybe show dashboard to try again
                 self._show_view("dashboard")
            else:
                 # Check if we are currently loading
                 if self.loading_overlay.winfo_viewable():
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
        self.results_view.grid_forget()
        self.loading_overlay.grid_forget()
        
        # Show selected
        if view_name == "dashboard":
            self.dashboard_view.grid(row=0, column=0, sticky="nsew")
        elif view_name == "results":
            self.results_view.grid(row=0, column=0, sticky="nsew")
        elif view_name == "loading":
            self.loading_overlay.grid(row=0, column=0, sticky="nsew")

    def _on_select_file(self):
        """Handle file selection from Dashboard."""
        filepath = filedialog.askopenfilename(
            title="Chọn một file Ebook", filetypes=[("Ebooks", "*.pdf *.epub")]
        )
        if not filepath:
            return
        self._start_parsing(filepath)

    def _start_parsing(self, filepath: str):
        """Shared logic to start parsing a file."""
        filename = Path(filepath).name
        self.current_filepath = filepath
        self.top_bar.set_file_path(filepath)
        
        # Switch to loading
        self._show_view("loading")
        self.loading_overlay.update_status(title=f"Đang phân tích file:\n{filename}...", progress=None)

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
            
            self.current_results = results
            
            if results.get('error'):
                 messagebox.showerror("Lỗi", f"Lỗi phân tích: {results.get('error')}")
                 self._show_view("dashboard")
                 return
            
            if self.current_results and self.current_results.get('content'):
                # SUCCESS: Add to History
                metadata = self.current_results.get('metadata', {})
                title = metadata.get('title', Path(self.current_filepath).name)
                self.history_manager.add_entry(self.current_filepath, title=title)
                
                self._show_view("results")
                self.results_view.show_results(self.current_results)
                
                # Update Sidebar State
                self.sidebar.show_active_book_controls()
                self.sidebar.set_active_button("results")
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

        # Check for overwrite (Main Thread UI interaction)
        output_name = Path(self.current_filepath).name
        full_output_path = Path(target_dir) / output_name.replace(" ", "_").replace(".epub", "").replace(".pdf", "")
        
        if full_output_path.exists():
            if not messagebox.askyesno(
                "Thư mục đã tồn tại", 
                f"Thư mục '{full_output_path.name}' đã tồn tại.\nBạn có muốn ghi đè (xóa và tạo lại) không?"
            ):
                return
        
        # Show Loading Overlay for Saving
        self._show_view("loading")
        self.loading_overlay.update_status(title="Đang lưu dữ liệu...", detail="Chuẩn bị...", progress=0.0)

        # Start Saving Thread
        threading.Thread(
            target=self._worker_save_content, 
            args=(self.current_results.get('content', []), Path(target_dir), Path(self.current_filepath).name),
            daemon=True
        ).start()

    def _worker_save_content(self, content, target_dir, book_name):
        """Worker thread for saving content."""
        def progress_adapter(percent, msg):
            # Update UI from worker thread safely
            self.after(0, self.loading_overlay.update_status, "Đang lưu dữ liệu...", msg, percent)

        success, message = storage_handler.save_as_folders(
            content, target_dir, book_name, progress_callback=progress_adapter
        )
        
        # Schedule completion on main thread
        self.after(0, self._on_save_complete, success, message)

    def _on_save_complete(self, success, message):
        """Handle save completion on main thread."""
        # Restore view (implicitly hides loading overlay, but we want to stay on results usually?)
        # Actually stay on results.
        self._show_view("results") # This hides loading overlay
        
        if success:
             output_path = message
             if messagebox.askyesno(
                "Trích xuất thành công",
                f"Đã lưu vào:\n{output_path}\nMở thư mục ngay?"
            ):
                self._open_folder(output_path)
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