# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/sidebar.py
# Version: 1.1.0
# Author: Antigravity
# Description: Sidebar navigation component with active book state management.
# --------------------------------------------------------------------------------

from typing import Callable, Optional
import customtkinter as ctk

class SidebarFrame(ctk.CTkFrame):
    """
    Left sidebar with navigation buttons.
    
    Attributes:
        on_navigate (Callable): Callback function for navigation events.
        on_close_book (Callable): Callback function for closing the book.
    """
    def __init__(self, master, on_navigate: Callable, on_close_book: Optional[Callable] = None, **kwargs):
        """
        Initialize the sidebar frame.

        Args:
            master: The parent widget.
            on_navigate (Callable): Function to call when navigation changes.
            on_close_book (Optional[Callable]): Function to call when closing the book.
            **kwargs: Additional arguments for CTkFrame.
        """
        super().__init__(master, width=200, corner_radius=0, **kwargs)
        self.on_navigate = on_navigate
        self.on_close_book = on_close_book
        self.grid_rowconfigure(6, weight=1) # Adjusted for new buttons

        # Logo / Title
        self.logo_label = ctk.CTkLabel(
            self, text="E-Extract", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # 1. Main Navigation
        self.btn_dashboard = self._create_nav_button("Dashboard", 1, "dashboard")
        self.btn_library = self._create_nav_button("Thư viện", 2, "library")
        self.btn_settings = self._create_nav_button("Cài đặt", 3, "settings")

        # 2. Active Book Section (Hidden by default)
        self.lbl_active_book = ctk.CTkLabel(
            self, text="Đang mở:", text_color="gray", anchor="w", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.btn_active_book = self._create_nav_button("📄 Hiện tại", 5, "results")
        self.btn_close_book = ctk.CTkButton(
            self,
            text="❌ Đóng sách",
            fg_color="transparent",
            text_color=("red", "#ff5555"),
            hover_color=("gray90", "gray20"),
            anchor="w",
            command=self._handle_close_book
        )

        # Bottom info
        self.version_label = ctk.CTkLabel(
            self, text="v1.0.0", text_color="gray", font=ctk.CTkFont(size=10)
        )
        self.version_label.grid(row=7, column=0, padx=20, pady=20)
        
        # Initial State
        self.hide_active_book_controls()

    def _create_nav_button(self, text: str, row: int, view_name: str) -> ctk.CTkButton:
        """Helper to create consistent navigation buttons."""
        btn = ctk.CTkButton(
            self,
            text=text,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=lambda: self.on_navigate(view_name)
        )
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        return btn
    
    def _handle_close_book(self) -> None:
        """Handle close book action."""
        if self.on_close_book:
            self.on_close_book()

    def set_active_button(self, view_name: str) -> None:
        """
        Highlight the active navigation button.
        
        Args:
            view_name (str): The name of the active view.
        """
        buttons = {
            "dashboard": self.btn_dashboard,
            "library": self.btn_library,
            "settings": self.btn_settings,
            "results": self.btn_active_book
        }
        
        for name, btn in buttons.items():
            if name == view_name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

    def show_active_book_controls(self, book_title: str = "Book") -> None:
        """
        Show the controls for the active book.
        
        Args:
            book_title (str): Title to display (unused currently, reserved for label update).
        """
        self.lbl_active_book.grid(row=4, column=0, sticky="ew", padx=20, pady=(15, 0))
        self.btn_active_book.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        self.btn_close_book.grid(row=6, column=0, sticky="ew", padx=10, pady=5)

    def hide_active_book_controls(self) -> None:
        """Hide the controls for the active book."""
        self.lbl_active_book.grid_remove()
        self.btn_active_book.grid_remove()
        self.btn_close_book.grid_remove()

