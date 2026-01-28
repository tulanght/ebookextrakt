# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/library_view.py
# Version: 1.0.0
# Author: Antigravity
# Description: Displays the Library of extracted books with search and management.
# --------------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox
from typing import Callable, List, Dict, Any
import customtkinter as ctk
from PIL import Image

class BookCard(ctk.CTkFrame):
    """
    A card widget representing a single book in the grid.
    """
    def __init__(self, master, book_data: Dict, on_click: Callable[[int], None], on_delete: Callable[[int], None], **kwargs):
        super().__init__(master, **kwargs)
        self.book_data = book_data
        self.on_click = on_click
        self.on_delete = on_delete
        
        self.item_id = book_data['id']
        title = book_data.get('title', 'Unknown Title')
        author = book_data.get('author', 'Unknown Author')
        
        # Style
        self.configure(fg_color=("gray85", "gray25"), corner_radius=10)
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Title (Clickable)
        self.title_label = ctk.CTkLabel(
            self, text=title, font=("Segoe UI", 16, "bold"), 
            anchor="w", justify="left", wraplength=180
        )
        self.title_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # Make card clickable
        self.title_label.bind("<Button-1>", self._handle_click_event)
        self.bind("<Button-1>", self._handle_click_event)
        
        # 2. Author
        self.author_label = ctk.CTkLabel(
            self, text=author, font=("Segoe UI", 12),
            text_color="gray", anchor="w"
        )
        self.author_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.author_label.bind("<Button-1>", self._handle_click_event)

        # 3. Actions Frame
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        # Delete Button
        self.btn_delete = ctk.CTkButton(
            self.actions_frame, text="Xóa", width=50, height=24,
            fg_color="transparent", border_width=1, border_color="red", text_color="red",
            hover_color="darkred",
            command=self._handle_delete
        )
        self.btn_delete.pack(side="right", padx=5)

    def _handle_click_event(self, event=None):
        if self.on_click:
            self.on_click(self.item_id)
            
    def _handle_delete(self):
        if self.on_delete:
            self.on_delete(self.item_id)


class LibraryView(ctk.CTkFrame):
    """
    The main view for the Library tab.
    Displays a grid of books and a detail view.
    """
    def __init__(self, master, db_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db_manager = db_manager
        
        # UI State
        self.books: List[Dict] = []
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 1. Top Bar (Search & Refresh)
        self.top_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        
        self.entry_search = ctk.CTkEntry(
            self.top_frame, placeholder_text="Tìm kiếm sách...", 
            textvariable=self.search_var, width=300
        )
        self.entry_search.pack(side="left", padx=10, pady=10)
        
        self.btn_refresh = ctk.CTkButton(
            self.top_frame, text="Làm mới", width=100,
            command=self.refresh_library
        )
        self.btn_refresh.pack(side="right", padx=10)
        
        # 2. Content Area (Scrollable Grid)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        
        # Setup Grid Columns for Book Cards
        self.scroll_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Initial Load
        self.refresh_library()

    def refresh_library(self):
        """Fetch books from DB and render."""
        query = self.search_var.get()
        if query:
            self.books = self.db_manager.search_books(query)
        else:
            self.books = self.db_manager.get_all_books()
            
        self._render_books()

    def _on_search_change(self, *args):
        self.refresh_library()

    def _render_books(self):
        """Render book cards."""
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.books:
            lbl = ctk.CTkLabel(self.scroll_frame, text="Không tìm thấy sách nào trong thư viện.")
            lbl.pack(pady=50)
            return

        # Render Grid (3 columns)
        cols = 3
        for i, book in enumerate(self.books):
            row = i // cols
            col = i % cols
            
            card = BookCard(
                self.scroll_frame, 
                book_data=book, 
                on_click=self._open_book_detail,
                on_delete=self._delete_book
            )
            card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

    def _delete_book(self, book_id: int):
        """Confirm and delete book."""
        if messagebox.askyesno("Xác nhận xóa", "Bạn có chắc muốn xóa sách này khỏi thư viện?\n(File gốc vẫn được giữ nguyên)"):
            self.db_manager.delete_book(book_id)
            self.refresh_library()

    def _open_book_detail(self, book_id: int):
        """
        Show detail view for the book. 
        For now, we'll create a Toplevel window or overlay.
        Overlay is better for integration.
        """
        book_details = self.db_manager.get_book_details(book_id)
        if not book_details:
            return
            
        # Create Overlay Window (Modal-like)
        BookDetailWindow(self, book_details)

class BookDetailWindow(ctk.CTkToplevel):
    """
    Popup window showing book chapters and articles.
    """
    def __init__(self, master, book_details: Dict):
        super().__init__(master)
        self.title(book_details.get('title', 'Chi tiết sách'))
        self.geometry("800x600")
        
        # Data
        self.chapters = book_details.get('chapters', [])
        
        # UI
        # Header
        lbl_title = ctk.CTkLabel(self, text=book_details.get('title', ''), font=("Segoe UI", 20, "bold"))
        lbl_title.pack(pady=(20, 5))
        
        lbl_author = ctk.CTkLabel(self, text=book_details.get('author', ''), font=("Segoe UI", 14))
        lbl_author.pack(pady=(0, 20))
        
        # Scrollable List of Content
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._render_content()
        
    def _render_content(self):
        for chapter in self.chapters:
            # Chapter Header
            chap_title = chapter.get('title', 'Unknown Chapter')
            frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(frame, text=chap_title, font=("Segoe UI", 16, "bold"), anchor="w").pack(fill="x")
            
            # Articles
            for article in chapter.get('articles', []):
                art_frame = ctk.CTkFrame(self.list_frame, fg_color=("gray90", "gray20"))
                art_frame.pack(fill="x", pady=2, padx=10)
                
                status = article.get('status', 'new')
                status_color = "gray" if status == 'new' else "green"
                
                # Status Dot
                canvas = ctk.CTkCanvas(art_frame, width=10, height=10, bg=art_frame._apply_appearance_mode(art_frame._fg_color), highlightthickness=0)
                canvas.create_oval(2, 2, 8, 8, fill=status_color)
                canvas.pack(side="left", padx=5)
                
                ctk.CTkLabel(art_frame, text=article.get('subtitle', 'No Subtitle'), anchor="w").pack(side="left", padx=5)
                
                # Future: Translate Button
                # ctk.CTkButton(art_frame, text="Dịch", width=50).pack(side="right", padx=5)
