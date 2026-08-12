# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/library_view.py
# Version: 2.0.0 (Phase 3B refactor)
# Author: Antigravity
# Description: Displays the Library of extracted books with search and management.
#              BookDetailWindow has been extracted to book_detail_window.py.
# --------------------------------------------------------------------------------

import tkinter as tk
from typing import Callable, List, Dict, Any
import customtkinter as ctk
from PIL import Image, ImageOps, ImageTk
from pathlib import Path
from .custom_dialog import ask_yes_no, show_info, show_warning, show_error
from ...core import webview_generator
import os
import webbrowser
import shutil
import datetime
import threading
import time
from .theme import Colors, Fonts, Spacing
from .editor_view import DualViewEditor
from .tooltip import ToolTip
from ...core.eta_calculator import calculate_book_eta, update_dynamic_wpm
from ...core.queue_manager import ChapterQueueManager, ChapterQueueItem, QueueStatus
from .book_detail_window import BookDetailWindow  # noqa: F401 — re-exported

class BookCard(ctk.CTkFrame):
    """
    A card widget representing a single book in the grid (Dark Navy theme).
    """
    def __init__(self, master, book_data: Dict, on_click: Callable[[int], None], on_delete: Callable[[int], None], **kwargs):
        super().__init__(
            master, 
            fg_color=Colors.BG_CARD, 
            corner_radius=Spacing.CARD_RADIUS, 
            border_width=1, 
            border_color=Colors.BORDER,
            **kwargs
        )
        self.book_data = book_data
        self.on_click = on_click
        self.on_delete = on_delete
        
        self.item_id = book_data['id']
        full_title = book_data.get('title', 'Unknown Title')
        author = book_data.get('author', 'Unknown Author')
        cover_path = book_data.get('cover_path', '')
        published_year = book_data.get('published_year', '')
        category = book_data.get('category', '')
        added_date = book_data.get('added_date', '')
        
        # Fixed card size
        self.configure(width=220, height=385)
        self.pack_propagate(False)
        
        # Hover Effect Triggers
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # ===== PACK LAYOUT (top to bottom) =====
        
        # 1. Cover Image — start with placeholder, load image asynchronously
        cover_w, cover_h = 200, 220
        self.lbl_cover = ctk.CTkLabel(
            self, text="📚", 
            font=Fonts.H3,
            fg_color=Colors.BG_APP,
            text_color=Colors.TEXT_MUTED,
            corner_radius=10,
            width=cover_w, height=cover_h
        )
        self.lbl_cover.pack(side="top", pady=(8, 4), padx=10)
        self._bind_click(self.lbl_cover)

        # Load cover async to avoid blocking main thread
        if cover_path and Path(cover_path).exists():
            threading.Thread(
                target=self._load_cover_async,
                args=(cover_path, cover_w, cover_h),
                daemon=True
            ).start()
        
        # 2. Title (truncated, max 2 lines)
        display_title = full_title
        if len(display_title) > 42:
            display_title = display_title[:39] + "..."
            
        self.title_label = ctk.CTkLabel(
            self, text=display_title, font=Fonts.BODY_BOLD, 
            text_color=Colors.TEXT_PRIMARY,
            anchor="center", justify="center", wraplength=190
        )
        self.title_label.pack(side="top", fill="x", padx=8, pady=(0, 2))
        self._bind_click(self.title_label)
        
        # Tooltip for full title
        if len(full_title) > 42:
             ToolTip(self.title_label, full_title)
        
        # 3. Author & Year
        author_text = author
        if published_year:
             author_text = f"{author} • {published_year}"
             
        self.author_label = ctk.CTkLabel(
            self, text=author_text, font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED
        )
        self.author_label.pack(side="top", fill="x", padx=8, pady=(0, 2))
        self._bind_click(self.author_label)

        # 4. Category tag (if present)
        if category:
            lbl_cat = ctk.CTkLabel(
                self, text=category, font=Fonts.TINY,
                fg_color=Colors.BG_APP, text_color=Colors.PRIMARY,
                corner_radius=4, padx=6, pady=2
            )
            lbl_cat.pack(side="top", pady=(0, 2))

        # 5. Added date (relative time)
        if added_date:
            date_display = self._format_relative_date(added_date)
            self.date_label = ctk.CTkLabel(
                self, text=f"📅 {date_display}", font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED
            )
            self.date_label.pack(side="top", pady=(0, 2))

        # 5b. Translation Progress Bar
        total_leaf = book_data.get('total_leaf', 0) or 0
        translated_count = book_data.get('translated_count', 0) or 0
        
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(side="top", fill="x", padx=10, pady=(0, 4))
        
        if total_leaf > 0:
            ratio = translated_count / total_leaf
            bar_color = Colors.SUCCESS if ratio >= 1.0 else Colors.PRIMARY
            prog_bar = ctk.CTkProgressBar(
                progress_frame, width=180, height=6,
                fg_color=Colors.BG_APP, progress_color=bar_color,
                corner_radius=3
            )
            prog_bar.set(ratio)
            prog_bar.pack(side="top")
            
            prog_text = f"{translated_count}/{total_leaf} bài đã dịch"
            lbl_prog = ctk.CTkLabel(
                progress_frame, text=prog_text, font=Fonts.TINY,
                text_color=bar_color if ratio >= 1.0 else Colors.TEXT_MUTED
            )
            lbl_prog.pack(side="top")
        else:
            ctk.CTkLabel(
                progress_frame, text="Chưa có nội dung", font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED
            ).pack(side="top")

        # 6. Delete Button (hidden by default, positioned top-right on hover)
        self.btn_delete = ctk.CTkButton(
            self, text="×", width=24, height=24,
            fg_color=Colors.BG_CARD_HOVER, border_color=Colors.DANGER, border_width=1,
            text_color=Colors.DANGER, hover_color=Colors.DANGER_HOVER,
            font=Fonts.BODY_BOLD, corner_radius=12,
            command=self._handle_delete
        )
        self.btn_delete.bind("<Enter>", self._on_enter)
        self.btn_delete.bind("<Leave>", self._on_leave)

    def _load_cover_async(self, cover_path: str, cover_w: int, cover_h: int):
        """Load book cover from disk in background thread, then update label on main thread."""
        try:
            img = Image.open(cover_path)
            img = ImageOps.fit(img, (cover_w * 2, cover_h * 2), method=Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(cover_w, cover_h))
            # Must update widget on main thread via after()
            if self.winfo_exists():
                self.after(0, lambda: self.lbl_cover.configure(image=ctk_img, text=""))
        except Exception:
            pass  # keep placeholder on error

    def _bind_click(self, widget):

        widget.bind("<Button-1>", self._handle_click_event)
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        self.configure(border_color=Colors.PRIMARY, fg_color=Colors.BG_CARD_HOVER)
        self.btn_delete.place(relx=1.0, rely=0.0, anchor="ne", x=-6, y=6)

    def _on_leave(self, event=None):
        self.configure(border_color=Colors.BORDER, fg_color=Colors.BG_CARD)
        self.btn_delete.place_forget()

    def _handle_click_event(self, event=None):
        if self.on_click:
            self.on_click(self.item_id)

    @staticmethod
    def _format_relative_date(date_str: str) -> str:
        """Format an ISO/SQLite timestamp into Vietnamese relative time."""
        try:
            dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.datetime.now(dt.tzinfo) if dt.tzinfo else datetime.datetime.now()
            delta = now - dt
            days = delta.days
            if days == 0:
                return "Hôm nay"
            elif days == 1:
                return "Hôm qua"
            elif days < 30:
                return f"{days} ngày trước"
            else:
                return dt.strftime("%d/%m/%Y")
        except Exception:
            return date_str[:10] if len(date_str) >= 10 else date_str
            
    def _handle_delete(self):
        if self.on_delete:
            self.on_delete(self.item_id)


class BookListRow(ctk.CTkFrame):
    """
    A list row widget representing a single book in List View.
    """
    def __init__(self, master, book_data: Dict, on_click: Callable[[int], None], on_delete: Callable[[int], None], **kwargs):
        super().__init__(
            master, 
            fg_color=Colors.BG_CARD, 
            corner_radius=Spacing.BUTTON_RADIUS, 
            border_width=1, 
            border_color=Colors.BORDER,
            height=60,
            **kwargs
        )
        self.pack_propagate(False)
        self.book_data = book_data
        self.on_click = on_click
        self.on_delete = on_delete
        self.item_id = book_data['id']
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        self.grid_columnconfigure(2, weight=1)
        
        cover_path = book_data.get('cover_path', '')
        self.lbl_cover = ctk.CTkLabel(self, text="📚", width=40, height=50, fg_color=Colors.BG_APP, corner_radius=4)
        self.lbl_cover.grid(row=0, column=0, padx=(10, 10), pady=5)
        self._bind_click(self.lbl_cover)
        
        if cover_path and Path(cover_path).exists():
            threading.Thread(target=self._load_cover_async, args=(cover_path,), daemon=True).start()
            
        title = book_data.get('title', 'Unknown Title')
        author = book_data.get('author', 'Unknown Author')
        
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=2, sticky="w", padx=10)
        
        lbl_title = ctk.CTkLabel(info_frame, text=title, font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY)
        lbl_title.pack(anchor="w")
        self._bind_click(lbl_title)
        
        lbl_author = ctk.CTkLabel(info_frame, text=author, font=Fonts.SMALL, text_color=Colors.TEXT_MUTED)
        lbl_author.pack(anchor="w")
        self._bind_click(lbl_author)

        total_leaf = book_data.get('total_leaf', 0) or 0
        translated = book_data.get('translated_count', 0) or 0
        prog_text = f"{translated}/{total_leaf}" if total_leaf > 0 else "N/A"
        
        ctk.CTkLabel(self, text=prog_text, font=Fonts.SMALL, text_color=Colors.TEXT_PRIMARY).grid(row=0, column=3, padx=20)
        
        self.btn_delete = ctk.CTkButton(
            self, text="×", width=30, height=30,
            fg_color="transparent", text_color=Colors.DANGER, hover_color=Colors.DANGER_HOVER,
            font=Fonts.BODY_BOLD, corner_radius=4, command=self._handle_delete
        )
        self.btn_delete.grid(row=0, column=4, padx=(0, 10))

    def _load_cover_async(self, cover_path: str):
        try:
            img = Image.open(cover_path)
            img = ImageOps.fit(img, (80, 100), method=Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 50))
            if self.winfo_exists():
                self.after(0, lambda: self.lbl_cover.configure(image=ctk_img, text=""))
        except Exception:
            pass
            
    def _bind_click(self, widget):
        widget.bind("<Button-1>", self._handle_click_event)
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        self.configure(border_color=Colors.PRIMARY, fg_color=Colors.BG_CARD_HOVER)

    def _on_leave(self, event=None):
        self.configure(border_color=Colors.BORDER, fg_color=Colors.BG_CARD)

    def _handle_click_event(self, event=None):
        if self.on_click:
            self.on_click(self.item_id)
            
    def _handle_delete(self):
        if self.on_delete:
            self.on_delete(self.item_id)


class LibraryView(ctk.CTkFrame):
    """
    The main view for the Library tab (Dark Navy).
    Displays a grid of books and a detail view.
    """
    def __init__(self, master, db_manager, settings_manager, translation_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db_manager = db_manager
        self.settings_manager = settings_manager
        self.translation_service = translation_service
        
        self.books: List[Dict] = []
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # 1. Top Bar (Search & Refresh)
        self.top_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 0))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        
        self.entry_search = ctk.CTkEntry(
            self.top_frame, placeholder_text="Tìm kiếm sách...", 
            textvariable=self.search_var, width=300,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=36, corner_radius=Spacing.BUTTON_RADIUS
        )
        self.entry_search.pack(side="left", padx=Spacing.MD, pady=Spacing.MD)
        
        # Refresh Button
        self.btn_refresh = ctk.CTkButton(
            self.top_frame, text="🔄 Làm mới", width=100,
            fg_color=Colors.BG_CARD, border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY, hover_color=Colors.BG_CARD_HOVER,
            command=self.refresh_library,
            height=36, corner_radius=Spacing.BUTTON_RADIUS
        )
        self.btn_refresh.pack(side="right", padx=Spacing.XL)

        # 1b. Filter Bar
        self.filter_frame = ctk.CTkFrame(self, height=40, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=Spacing.MD, pady=(0, Spacing.MD))
        
        self.filter_status_var = tk.StringVar(value="Tất cả")
        self.seg_filter = ctk.CTkSegmentedButton(
            self.filter_frame, values=["Tất cả", "Chưa dịch", "Đang dịch", "Đã xong"],
            variable=self.filter_status_var, command=self._on_filter_change,
            font=Fonts.SMALL, selected_color=Colors.PRIMARY, selected_hover_color=Colors.PRIMARY_HOVER
        )
        self.seg_filter.pack(side="left", padx=0)

        self.sort_var = tk.StringVar(value="Mới thêm ↓")
        self.opt_sort = ctk.CTkOptionMenu(
            self.filter_frame, values=["Mới thêm ↓", "Cũ nhất ↑", "Tên A→Z", "% Dịch ↓"],
            variable=self.sort_var, command=self._on_filter_change,
            font=Fonts.SMALL, fg_color=Colors.BG_INPUT, button_color=Colors.BORDER,
            button_hover_color=Colors.PRIMARY, width=140
        )
        self.opt_sort.pack(side="left", padx=Spacing.MD)

        self.view_mode_var = tk.StringVar(value="Card")
        self.btn_view_mode = ctk.CTkButton(
            self.filter_frame, text="📋 List View", width=100,
            fg_color="transparent", border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY, hover_color=Colors.BG_CARD_HOVER,
            command=self._toggle_view_mode,
            font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS
        )
        self.btn_view_mode.pack(side="right", padx=0)
        
        # 2. Content Area (Scrollable Grid)
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.BORDER,
            scrollbar_button_hover_color=Colors.TEXT_MUTED
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._page = 1  # current page (how many PAGE_SIZE blocks shown)
        self.PAGE_SIZE = 20  # books per page

        self.refresh_library()

    def _on_filter_change(self, *args):
        self._page = 1
        self._render_books()

    def _toggle_view_mode(self):
        current = self.view_mode_var.get()
        if current == "Card":
            self.view_mode_var.set("List")
            self.btn_view_mode.configure(text="🔲 Card View")
        else:
            self.view_mode_var.set("Card")
            self.btn_view_mode.configure(text="📋 List View")
        self._page = 1
        self._render_books()

    def refresh_library(self):
        self._page = 1  # reset pagination
        query = self.search_var.get()
        if query:
            self.all_books = self.db_manager.search_books(query)
        else:
            self.all_books = self.db_manager.get_all_books()

        self._render_books()

    def _on_search_change(self, *args):
        if hasattr(self, '_search_after_id'):
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self.refresh_library)

    def _render_books(self):
        """Render paginated book grid — applies in-memory filters first."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not hasattr(self, 'all_books'):
            self.all_books = []

        # 1. Apply in-memory filter
        status_filter = self.filter_status_var.get()
        filtered_books = []
        for b in self.all_books:
            total = b.get('total_leaf', 0) or 0
            translated = b.get('translated_count', 0) or 0
            if status_filter == "Chưa dịch":
                if translated == 0: filtered_books.append(b)
            elif status_filter == "Đang dịch":
                if 0 < translated < total: filtered_books.append(b)
            elif status_filter == "Đã xong":
                if total > 0 and translated >= total: filtered_books.append(b)
            else:
                filtered_books.append(b)

        # 2. Apply in-memory sort
        sort_mode = self.sort_var.get()
        if sort_mode == "Cũ nhất ↑":
            filtered_books.sort(key=lambda x: x.get('added_date', ''), reverse=False)
        elif sort_mode == "Tên A→Z":
            filtered_books.sort(key=lambda x: x.get('title', '').lower())
        elif sort_mode == "% Dịch ↓":
            def get_pct(b):
                t = b.get('total_leaf', 0) or 0
                return (b.get('translated_count', 0) or 0) / t if t > 0 else 0
            filtered_books.sort(key=get_pct, reverse=True)
        else: # Mới thêm ↓
            filtered_books.sort(key=lambda x: x.get('added_date', ''), reverse=True)

        self.filtered_books = filtered_books

        if not self.filtered_books:
            ctk.CTkLabel(
                self.scroll_frame, text="Không tìm thấy sách nào phù hợp.",
                text_color=Colors.TEXT_MUTED, font=Fonts.BODY
            ).pack(pady=50)
            return

        is_list_view = self.view_mode_var.get() == "List"
        visible = self.filtered_books[:self._page * self.PAGE_SIZE]

        if is_list_view:
            self.scroll_frame.grid_columnconfigure((0, 1, 2, 3), weight=0)
            self.scroll_frame.grid_columnconfigure(0, weight=1)
            for i, book in enumerate(visible):
                row_ui = BookListRow(
                    self.scroll_frame, book_data=book,
                    on_click=self._open_book_detail,
                    on_delete=self._delete_book
                )
                row_ui.grid(row=i, column=0, sticky="ew", padx=Spacing.MD, pady=4)
        else:
            self.scroll_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
            cols = 4
            for i, book in enumerate(visible):
                row_ = i // cols
                col_ = i % cols
                card = BookCard(
                    self.scroll_frame,
                    book_data=book,
                    on_click=self._open_book_detail,
                    on_delete=self._delete_book
                )
                card.grid(row=row_, column=col_, sticky="n", padx=Spacing.MD, pady=Spacing.MD)

        # Load More button
        if len(self.filtered_books) > self._page * self.PAGE_SIZE:
            total_remaining = len(self.filtered_books) - self._page * self.PAGE_SIZE
            last_row = len(visible) if is_list_view else (len(visible) - 1) // 4 + 1
            col_span = 1 if is_list_view else 4
            ctk.CTkButton(
                self.scroll_frame,
                text=f"⬇ Tải thêm ({total_remaining} sách còn lại)",
                fg_color=Colors.BG_CARD, border_width=1, border_color=Colors.BORDER,
                text_color=Colors.TEXT_PRIMARY, hover_color=Colors.BG_CARD_HOVER,
                font=Fonts.BODY, corner_radius=Spacing.BUTTON_RADIUS,
                command=self._load_more
            ).grid(row=last_row, column=0, columnspan=col_span, pady=Spacing.XL, padx=Spacing.XL, sticky="ew")

    def _load_more(self):
        """Increment page and re-render to show more books."""
        self._page += 1
        self._render_books()

    def _delete_book(self, book_id: int):
        if ask_yes_no(self, "Xác nhận xóa", "Bạn có chắc muốn xóa sách này khỏi thư viện?\n(File gốc vẫn được giữ nguyên)", is_danger=True):
            self.db_manager.delete_book(book_id)
            self.refresh_library()

    def _open_book_detail(self, book_id: int):
        book_details = self.db_manager.get_book_details(book_id)
        if not book_details:
            return
            
        BookDetailWindow(self, book_details, self.translation_service, self.db_manager, self.settings_manager)


