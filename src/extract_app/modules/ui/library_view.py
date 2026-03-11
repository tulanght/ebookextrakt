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
from PIL import Image, ImageOps, ImageTk
from pathlib import Path
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
        self.configure(width=220, height=360)
        self.pack_propagate(False)
        
        # Hover Effect Triggers
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # ===== PACK LAYOUT (top to bottom) =====
        
        # 1. Cover Image
        self.cover_image = None
        cover_w, cover_h = 200, 220
        if cover_path and Path(cover_path).exists():
            try:
                img = Image.open(cover_path)
                # Provide a 2x resolution source so CTkImage has enough pixels for HiDPI
                img = ImageOps.fit(img, (cover_w * 2, cover_h * 2), method=Image.LANCZOS)
                self.cover_image = ctk.CTkImage(light_image=img, dark_image=img, size=(cover_w, cover_h))
            except Exception as e:
                print(f"Error loading cover: {e}")
        
        if self.cover_image:
            self.lbl_cover = ctk.CTkLabel(self, text="", image=self.cover_image, width=cover_w, height=cover_h)
        else:
            self.lbl_cover = ctk.CTkLabel(
                self, text="📚\nNo Cover", 
                font=Fonts.H3,
                fg_color=Colors.BG_APP,
                text_color=Colors.TEXT_MUTED,
                corner_radius=10,
                width=cover_w, height=cover_h
            )
            
        self.lbl_cover.pack(side="top", pady=(8, 4), padx=10)
        self._bind_click(self.lbl_cover)
        
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

        # 6. Delete Button (always at the very bottom)
        self.btn_delete = ctk.CTkButton(
            self, text="🗑 Xóa", width=60, height=24,
            fg_color="transparent", text_color=Colors.DANGER,
            hover_color=Colors.DANGER_HOVER,
            font=Fonts.TINY,
            command=self._handle_delete
        )
        self.btn_delete.pack(side="bottom", pady=(0, 8))

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

    @staticmethod
    def _format_relative_date(date_str: str) -> str:
        """Format an ISO/SQLite timestamp into Vietnamese relative time."""
        try:
            # SQLite CURRENT_TIMESTAMP format: "YYYY-MM-DD HH:MM:SS"
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
        self.grid_rowconfigure(1, weight=1)
        
        # 1. Top Bar (Search & Refresh)
        self.top_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, Spacing.MD))
        
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
        
        # 2. Content Area (Scrollable Grid)
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.BORDER,
            scrollbar_button_hover_color=Colors.TEXT_MUTED
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure((0, 1, 2, 3), weight=1) # 4 columns looks better on large screens

        self.refresh_library()

    def refresh_library(self):
        query = self.search_var.get()
        if query:
            self.books = self.db_manager.search_books(query)
        else:
            self.books = self.db_manager.get_all_books()
            
        self._render_books()

    def _on_search_change(self, *args):
        self.refresh_library()

    def _render_books(self):
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.books:
            lbl = ctk.CTkLabel(
                self.scroll_frame, text="Không tìm thấy sách nào trong thư viện.",
                text_color=Colors.TEXT_MUTED, font=Fonts.BODY
            )
            lbl.pack(pady=50)
            return

        # Render Grid (4 columns)
        cols = 4
        for i, book in enumerate(self.books):
            row = i // cols
            col = i % cols
            
            card = BookCard(
                self.scroll_frame, 
                book_data=book, 
                on_click=self._open_book_detail,
                on_delete=self._delete_book
            )
            card.grid(row=row, column=col, sticky="n", padx=Spacing.MD, pady=Spacing.MD)

    def _delete_book(self, book_id: int):
        if messagebox.askyesno("Xác nhận xóa", "Bạn có chắc muốn xóa sách này khỏi thư viện?\n(File gốc vẫn được giữ nguyên)"):
            self.db_manager.delete_book(book_id)
            self.refresh_library()

    def _open_book_detail(self, book_id: int):
        book_details = self.db_manager.get_book_details(book_id)
        if not book_details:
            return
            
        BookDetailWindow(self, book_details, self.translation_service, self.db_manager, self.settings_manager)

    def _open_settings(self):
        from .settings_window import SettingsWindow
        SettingsWindow(self, self.settings_manager, self.translation_service)

class BookDetailWindow(ctk.CTkToplevel):
    """
    Popup window showing book chapters and articles (Dark Navy theme).
    """
    def __init__(self, master, book_details: Dict, translation_service, db_manager, settings_manager):
        super().__init__(master, fg_color=Colors.BG_APP)
        self.title(book_details.get('title', 'Chi tiết sách'))
        self.geometry("900x700")
        
        self.translation_service = translation_service
        self.db_manager = db_manager
        self.settings_manager = settings_manager
        
        # Data
        self.book_id = book_details.get('id')
        self.chapters = book_details.get('chapters', [])
        
        # Chapter Queue Manager (one per open book window)
        self.queue_manager = ChapterQueueManager(
            translation_service=translation_service,
            db_manager=db_manager,
            settings_manager=settings_manager,
            on_item_done=lambda art_id, ok: self.after(0, lambda: self._on_queue_item_done(art_id, ok)),
            on_queue_done=lambda: self.after(0, self._on_queue_done),
            on_status_change=lambda s: self.after(0, lambda: self._on_queue_status_change(s)),
        )
        
        # UI
        # Header
        lbl_title = ctk.CTkLabel(
            self, text=book_details.get('title', ''), 
            font=Fonts.H2, text_color=Colors.TEXT_PRIMARY
        )
        lbl_title.pack(pady=(Spacing.XL, Spacing.SM))
        
        lbl_author = ctk.CTkLabel(
            self, text=book_details.get('author', ''), 
            font=Fonts.BODY, text_color=Colors.TEXT_MUTED
        )
        lbl_author.pack(pady=(0, Spacing.XL))
        
        # Tools Bar
        self.tools_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tools_frame.pack(fill="x", padx=Spacing.XL, pady=(0, Spacing.MD))
        
        self.btn_webview = ctk.CTkButton(
            self.tools_frame, text="📖 Đọc Thử (Webview)", 
            font=Fonts.BODY_BOLD, fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY,
            hover_color=Colors.PRIMARY_HOVER, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._generate_and_open_webview
        )
        self.btn_webview.pack(side="left")
        
        self.btn_ai_glossary = ctk.CTkButton(
            self.tools_frame, text="🪄 AI Tạo Từ Vựng", 
            font=Fonts.BODY_BOLD, fg_color="transparent", border_width=1, border_color=Colors.WARNING,
            text_color=Colors.WARNING, hover_color=Colors.BG_CARD_HOVER, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._open_ai_glossary_modal
        )
        self.btn_ai_glossary.pack(side="left", padx=Spacing.MD)
        
        # ETA Label — estimated time to translate remaining chapters
        engine = settings_manager.get("translation_engine", "cloud")
        wpm_key = f"{engine}_llm_wpm"
        default_wpm = 6000 if engine == "cloud" else 180
        wpm = int(settings_manager.get(wpm_key, default_wpm))
        
        chapters = book_details.get('chapters', [])
        eta_text = calculate_book_eta(chapters, wpm=wpm, engine=engine)
        self.lbl_eta = ctk.CTkLabel(
            self.tools_frame,
            text=f"⏱ Ước tính dịch: {eta_text}",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED
        )
        self.lbl_eta.pack(side="right", padx=Spacing.MD)
        
        # ── Queue Control Bar ──────────────────────────────────────────
        self.queue_bar = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=8)
        self.queue_bar.pack(fill="x", padx=Spacing.XL, pady=(0, Spacing.SM))
        
        # Queue status label
        self.lbl_queue_status = ctk.CTkLabel(
            self.queue_bar, text="📋 Hàng đợi: Chưa có bài nào",
            font=Fonts.SMALL, text_color=Colors.TEXT_MUTED
        )
        self.lbl_queue_status.pack(side="left", padx=Spacing.MD, pady=Spacing.SM)
        
        # Stop button
        self.btn_queue_stop = ctk.CTkButton(
            self.queue_bar, text="⏹ Dừng", width=70, height=26,
            fg_color="transparent", border_width=1, border_color=Colors.DANGER,
            text_color=Colors.DANGER, hover_color=Colors.BG_CARD_HOVER,
            font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._stop_queue
        )
        self.btn_queue_stop.pack(side="right", padx=2, pady=Spacing.SM)
        
        # Pause / Resume button
        self.btn_queue_pause = ctk.CTkButton(
            self.queue_bar, text="⏸ Tạm dừng", width=90, height=26,
            fg_color="transparent", border_width=1, border_color=Colors.WARNING,
            text_color=Colors.WARNING, hover_color=Colors.BG_CARD_HOVER,
            font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._toggle_pause_queue
        )
        self.btn_queue_pause.pack(side="right", padx=2, pady=Spacing.SM)
        
        # Start queue button
        self.btn_queue_start = ctk.CTkButton(
            self.queue_bar, text="▶ Bắt đầu Queue", width=120, height=26,
            fg_color=Colors.SUCCESS, text_color="white",
            hover_color="#1a8a4a",
            font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._start_queue
        )
        self.btn_queue_start.pack(side="right", padx=(2, Spacing.MD), pady=Spacing.SM)

        # Scrollable List of Content
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS,
            scrollbar_button_color=Colors.BORDER, scrollbar_button_hover_color=Colors.TEXT_MUTED
        )
        self.list_frame.pack(fill="both", expand=True, padx=Spacing.XL, pady=Spacing.XL)
        
        self._render_content()
        
        # Ensure window appears on top (Windows fix)
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        self.focus_force()
        
    def _render_content(self):
        # Refetch data to get updated status
        if self.book_id:
            fresh_data = self.db_manager.get_book_details(self.book_id)
            if fresh_data:
                self.chapters = fresh_data.get('chapters', [])
        
        if not self.winfo_exists() or not self.list_frame.winfo_exists():
            return

        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for chapter in self.chapters:
            all_articles = chapter.get('articles', [])
            
            # Calculate chapter-level totals
            total_words = sum(a.get('word_count', 0) or 0 for a in all_articles)
            total_translated = sum(1 for a in all_articles if a.get('status') == 'translated' and a.get('is_leaf', 1))
            total_leaf = sum(1 for a in all_articles if a.get('is_leaf', 1))
            
            # ── Chapter Header ──
            chap_title = chapter.get('title', 'Unknown Chapter')
            chap_frame = ctk.CTkFrame(self.list_frame, fg_color=Colors.BG_CARD_HOVER, corner_radius=Spacing.BUTTON_RADIUS)
            chap_frame.pack(fill="x", pady=(Spacing.MD, Spacing.XS), padx=0)
            
            ctk.CTkLabel(
                chap_frame, text=f"📂 {chap_title}", font=Fonts.H3, 
                text_color=Colors.TEXT_PRIMARY, anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=Spacing.MD, pady=Spacing.SM)

            # Chapter stats
            progress_text = f"{total_translated}/{total_leaf}" if total_leaf > 0 else "0"
            stats_text = f"{total_words:,} từ | {progress_text} đã dịch"
            ctk.CTkLabel(
                chap_frame, text=stats_text, font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED
            ).pack(side="right", padx=Spacing.MD, pady=Spacing.SM)
            
            # ── Separate parent containers (is_leaf=0) from leaf articles (is_leaf=1) ──
            parent_articles = [a for a in all_articles if not a.get('is_leaf', 1)]
            leaf_articles = [a for a in all_articles if a.get('is_leaf', 1)]
            
            # If there are parent (container) articles with children, build hierarchy
            if parent_articles and leaf_articles:
                for parent in parent_articles:
                    parent_word_count = parent.get('word_count', 0) or 0
                    # Show parent as a sub-section header  
                    if parent_word_count > 0:
                        self._render_article_row(parent, indent=Spacing.MD, is_parent=True)
                
                # Show leaf articles indented
                for article in leaf_articles:
                    self._render_article_row(article, indent=Spacing.XL + Spacing.MD)
            else:
                # Flat articles (no hierarchy) — render all directly
                for article in all_articles:
                    self._render_article_row(article, indent=Spacing.MD)
                     
    def _render_article_row(self, article, indent=0, is_parent=False):
        """Renders a single article row with status, title, word count, and action buttons."""
        status = article.get('status', 'new')
        is_translated = status == 'translated'
        is_leaf = article.get('is_leaf', 1)
        
        if is_parent:
            # Parent article: show as a sub-group header with translate button
            art_frame = ctk.CTkFrame(
                self.list_frame, fg_color=Colors.BG_CARD,
                corner_radius=Spacing.BUTTON_RADIUS
            )
            art_frame.pack(fill="x", pady=(Spacing.SM, 1), padx=indent)
            
            word_count = article.get('word_count', 0) or 0
            ctk.CTkLabel(
                art_frame, text=f"  📄 {article.get('subtitle', '')}", 
                font=Fonts.BODY_BOLD, text_color=Colors.TEXT_SECONDARY, anchor="w"
            ).pack(side="left", padx=Spacing.SM, fill="x", expand=True)
            
            # Right side: word count + action buttons
            right_frame = ctk.CTkFrame(art_frame, fg_color="transparent")
            right_frame.pack(side="right", fill="y", padx=Spacing.SM)
            
            ctk.CTkLabel(
                right_frame, text=f"{word_count:,} từ (giới thiệu)",
                text_color=Colors.TEXT_MUTED, font=Fonts.TINY
            ).pack(side="left", padx=(Spacing.SM, Spacing.MD))
            
            if is_translated:
                ctk.CTkButton(
                    right_frame, text="Biên tập", width=72, height=26,
                    fg_color="transparent", border_width=1, border_color=Colors.SUCCESS,
                    text_color=Colors.SUCCESS, hover_color=Colors.BG_CARD_HOVER,
                    font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                    command=lambda a=article: self._open_dual_view(a)
                ).pack(side="left", padx=2, pady=4)
            elif word_count > 50:
                ctk.CTkButton(
                    right_frame, text="📥 Dịch Lưu trữ", width=110, height=26,
                    fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY, hover_color=Colors.PRIMARY_HOVER,
                    font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                    command=lambda a=article: self._translate_article(a)
                ).pack(side="left", padx=2, pady=4)
            return
        
        # Leaf article row
        art_frame = ctk.CTkFrame(
            self.list_frame, fg_color=Colors.BG_APP, 
            corner_radius=Spacing.BUTTON_RADIUS
        )
        art_frame.pack(fill="x", pady=2, padx=indent)
        
        status_color = Colors.SUCCESS if is_translated else Colors.TEXT_MUTED
        
        # Status Dot
        canvas = ctk.CTkCanvas(art_frame, width=10, height=10, bg=Colors.BG_APP, highlightthickness=0)
        canvas.create_oval(2, 2, 8, 8, fill=status_color)
        canvas.pack(side="left", padx=Spacing.SM)
        
        # Right Side Container (Meta + Buttons)
        right_frame = ctk.CTkFrame(art_frame, fg_color="transparent")
        right_frame.pack(side="right", fill="y", padx=Spacing.SM)

        # Word Count Display
        word_count = article.get('word_count', 0) or 0
        translated_at = article.get('translated_at')
        
        meta_str = f"{word_count:,} từ"
        if translated_at:
            meta_str += f" | {str(translated_at)[:10]}"
            
        ctk.CTkLabel(
            right_frame, text=meta_str, text_color=Colors.TEXT_MUTED, font=Fonts.TINY
        ).pack(side="left", padx=(Spacing.SM, Spacing.MD))
        
        # Title & Status (Left aligned)
        ctk.CTkLabel(
            art_frame, text=article.get('subtitle', 'No Subtitle'), 
            font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left", padx=Spacing.SM, fill="x", expand=True)

        # Translate Button / View Button (only for leaf articles)
        if is_leaf:
            if is_translated:
                 # Edit button
                 ctk.CTkButton(
                     right_frame, text="Biên tập", width=72, height=26,
                     fg_color="transparent", border_width=1, border_color=Colors.SUCCESS,
                     text_color=Colors.SUCCESS, hover_color=Colors.BG_CARD_HOVER,
                     font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                     command=lambda a=article: self._open_dual_view(a)
                 ).pack(side="left", padx=2, pady=4)
                 
                 engine = self.settings_manager.get("translation_engine", "cloud")
                 btn_state = "normal" if engine == "cloud" else "disabled"
                 
                 # Website variant button
                 has_web = bool(article.get('website_text'))
                 web_fg = Colors.BG_CARD if has_web else "transparent"
                 ctk.CTkButton(
                     right_frame, text="🌐", width=32, height=26,
                     state=btn_state,
                     fg_color=web_fg, border_width=1, border_color=Colors.PRIMARY,
                     text_color=Colors.PRIMARY, hover_color=Colors.BG_CARD_HOVER,
                     font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                     command=lambda a=article: self._transform_article(a, 'website')
                 ).pack(side="left", padx=2, pady=4)
                 
                 # Facebook variant button
                 has_fb = bool(article.get('facebook_text'))
                 fb_fg = Colors.BG_CARD if has_fb else "transparent"
                 ctk.CTkButton(
                     right_frame, text="📱", width=32, height=26,
                     state=btn_state,
                     fg_color=fb_fg, border_width=1, border_color=Colors.WARNING,
                     text_color=Colors.WARNING, hover_color=Colors.BG_CARD_HOVER,
                     font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                     command=lambda a=article: self._transform_article(a, 'facebook')
                 ).pack(side="left", padx=2, pady=4)
                 
                 # Retranslate button
                 ctk.CTkButton(
                     right_frame, text="🔄 Dịch Lại", width=80, height=26,
                     fg_color="transparent", border_width=1, border_color=Colors.WARNING,
                     text_color=Colors.WARNING, hover_color=Colors.BG_CARD_HOVER,
                     font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                     command=lambda a=article: self._translate_article(a, force_retranslate=True)
                 ).pack(side="left", padx=2, pady=4)
            else:
                 # Untranslated: show Translate and Queue toggle buttons
                 ctk.CTkButton(
                     right_frame, text="📥 Dịch Lưu trữ", width=110, height=26, 
                     fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY, hover_color=Colors.PRIMARY_HOVER,
                     font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                     command=lambda a=article: self._translate_article(a)
                 ).pack(side="left", padx=2, pady=4)
                 
                 # Queue toggle button
                 article_id = article.get('id')
                 is_queued = self.queue_manager.is_queued(article_id)
                 q_text = "✖ Hủy Queue" if is_queued else "➕ Thêm Queue"
                 q_color = Colors.DANGER if is_queued else Colors.TEXT_MUTED
                 ctk.CTkButton(
                     right_frame, text=q_text, width=90, height=26,
                     fg_color="transparent", border_width=1, border_color=q_color,
                     text_color=q_color, hover_color=Colors.BG_CARD_HOVER,
                     font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                     command=lambda a=article: self._toggle_article_queue(a)
                 ).pack(side="left", padx=2, pady=4)
        else:
            # Container articles
            ctk.CTkLabel(
                right_frame, text="(Mục lục)", 
                text_color=Colors.TEXT_MUTED, font=Fonts.TINY
            ).pack(side="left", padx=Spacing.MD, pady=2)
                     
    # ─────────────────────────────────────────────────────────────────
    # Queue Control Methods (Task 3.2 + 3.3)
    # ─────────────────────────────────────────────────────────────────

    def _toggle_article_queue(self, article: Dict) -> None:
        """Add or remove a single article from the translation queue."""
        article_id = article.get('id')
        if self.queue_manager.is_queued(article_id):
            self.queue_manager.remove(article_id)
        else:
            content = self.db_manager.get_article_content(article_id) or ""
            if not content:
                from tkinter import messagebox
                messagebox.showwarning("Nội dung trống", "Bài viết này không có nội dung để dịch.", parent=self)
                return
            item = ChapterQueueItem(
                article_id=article_id,
                subtitle=article.get('subtitle', ''),
                word_count=article.get('word_count', 0) or 0,
                content=content,
            )
            self.queue_manager.enqueue(item)
        # Re-render to reflect updated queue state
        self._render_content()
        self._update_queue_status_label()

    def _start_queue(self) -> None:
        """Start processing the chapter queue."""
        if not self.queue_manager.pending_ids:
            from tkinter import messagebox
            messagebox.showinfo("Hàng đợi trống", "Hãy thêm ít nhất 1 bài vào hàng đợi trước bằng nút '➕ Thêm Queue'.", parent=self)
            return
        self.queue_manager.start()

    def _toggle_pause_queue(self) -> None:
        """Toggle between Pause and Resume."""
        if self.queue_manager.status == "paused":
            self.queue_manager.resume()
        else:
            self.queue_manager.pause()

    def _stop_queue(self) -> None:
        """Stop and clear the entire queue."""
        self.queue_manager.stop()
        self._render_content()  # Refresh buttons to remove queue indicators
        self._update_queue_status_label()

    def _on_queue_item_done(self, article_id: int, success: bool) -> None:
        """Called on main thread when a queue item finishes."""
        self._render_content()
        self._refresh_eta()
        self._update_queue_status_label()

    def _on_queue_done(self) -> None:
        """Called on main thread when the entire queue is exhausted."""
        self._update_queue_status_label()
        from tkinter import messagebox
        messagebox.showinfo("✅ Hoàn tất", "Hàng đợi dịch đã xử lý xong tất cả các bài!", parent=self)

    def _on_queue_status_change(self, status: str) -> None:
        """Update the Pause button label based on queue status."""
        if status == "paused":
            self.btn_queue_pause.configure(text="▶ Tiếp tục")
        else:
            self.btn_queue_pause.configure(text="⏸ Tạm dừng")
        self._update_queue_status_label()

    def _update_queue_status_label(self) -> None:
        """Refresh the queue status label text."""
        if not self.winfo_exists() or not hasattr(self, 'lbl_queue_status'):
            return
        count = len(self.queue_manager.pending_ids)
        status = self.queue_manager.status
        if count == 0:
            text = "📋 Hàng đợi: Chưa có bài nào"
        elif status == "running":
            text = f"🖥️ Đang dịch... ({count} bài còn lại)"
        elif status == "paused":
            text = f"⏸ Tạm dừng ({count} bài còn lại)"
        else:
            text = f"📋 Hàng đợi: {count} bài chờ dịch"
        self.lbl_queue_status.configure(text=text)

    def _open_ai_glossary_modal(self):
        """Opens a modal to configure and trigger AI Glossary extraction."""
        if not self.translation_service.api_key:
             messagebox.showwarning("Thiếu API Key", "Vui lòng nhập Cloud API Key (Gemini) trong phần Cài đặt trước.", parent=self)
             return

        # Fetch existing categories from GlossaryManager
        categories = self.translation_service.glossary_manager.get_categories()
        
        modal = ctk.CTkToplevel(self)
        modal.title("🪄 Tự động trích xuất Từ Vựng bằng AI")
        modal.geometry("480x380")
        modal.transient(self)
        modal.grab_set()
        modal.config(bg=Colors.BG_APP)
        
        ctk.CTkLabel(
            modal, text="AI (Gemini) sẽ đọc một phần nội dung sách để tự động tìm và\ntạo danh sách 30-50 từ khóa/thuật ngữ quan trọng nhất.",
            font=Fonts.BODY, text_color=Colors.TEXT_MUTED, justify="left"
        ).pack(pady=(20, 10), padx=20, fill="x")
        
        # Form frame
        form = ctk.CTkFrame(modal, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=10)
        
        # Subject Input
        ctk.CTkLabel(form, text="Chủ đề sách (Để AI dịch chuẩn ngữ cảnh):", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", pady=5)
        entry_subject = ctk.CTkEntry(form, width=300, fg_color=Colors.BG_INPUT, border_color=Colors.BORDER)
        entry_subject.insert(0, self.title()[:30] + "...") # Default suggestion
        entry_subject.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        # Category Combobox (Target)
        ctk.CTkLabel(form, text="Lưu vào danh mục từ vựng:", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).grid(row=2, column=0, sticky="w", pady=5)
        
        combo_category = ctk.CTkComboBox(
            form, width=300, values=categories if categories else ["Sách mới"],
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, button_color=Colors.PRIMARY
        )
        if categories:
            # Suggest current active or first
            active = self.translation_service.glossary_manager.get_active_category()
            combo_category.set(active if active else categories[0])
        else:
            combo_category.set("Sách mới")
        combo_category.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        
        # Action Buttons
        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        def on_start():
            subject = entry_subject.get().strip()
            target_cat = combo_category.get().strip()
            if not subject or not target_cat:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng điền đủ Chủ đề và Danh mục.", parent=modal)
                return
            modal.destroy()
            self._start_ai_glossary_extraction(subject, target_cat)
            
        ctk.CTkButton(
            btn_frame, text="Bắt đầu Trích xuất 🚀", width=140, height=32,
            fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY,
            command=on_start
        ).pack(side="right")
        
        ctk.CTkButton(
            btn_frame, text="Hủy", width=80, height=32,
            fg_color="transparent", border_color=Colors.BORDER, border_width=1, text_color=Colors.TEXT_MUTED,
            command=modal.destroy
        ).pack(side="right", padx=10)

    def _start_ai_glossary_extraction(self, subject: str, target_category: str):
        """Samples text and sends to translation service in background."""
        import threading
        
        # 1. Sample ~15,000 characters from the book's articles
        sample_text = ""
        for chapter in self.chapters:
            for article in chapter.get('articles', []):
                content = self.db_manager.get_article_content(article['id'])
                if content:
                    sample_text += content + "\n\n"
                if len(sample_text) > 15000:
                    break
            if len(sample_text) > 15000:
                break
                
        if len(sample_text) < 500:
            messagebox.showwarning("Cảnh báo", "Sách này quá ngắn hoặc chưa có chữ để trích xuất.", parent=self)
            return
            
        # 2. Setup Loading UI
        self.loading_win = ctk.CTkToplevel(self)
        self.loading_win.title("🪄 AI đang tạo Từ Vựng...")
        self.loading_win.geometry("380x130")
        self.loading_win.transient(self)
        self.loading_win.grab_set()
        
        ctk.CTkLabel(self.loading_win, text=f"Thu thập mẫu {len(sample_text[:15000]):,} ký tự... Đang phân tích...", font=("Segoe UI", 12)).pack(pady=(20, 5))
        self.progress_bar = ctk.CTkProgressBar(self.loading_win, mode="indeterminate", width=250)
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()
        
        # 3. Worker task
        def worker():
            terms, err = self.translation_service.extract_glossary_from_text(sample_text, subject)
            self.after(0, lambda: self._on_glossary_extraction_complete(terms, err, target_category))
            
        threading.Thread(target=worker, daemon=True).start()

    def _on_glossary_extraction_complete(self, terms: list, error: str, target_category: str):
        """Callback to save extracted terms."""
        if hasattr(self, 'loading_win') and self.loading_win.winfo_exists():
            self.loading_win.destroy()
            
        if error or not terms:
            messagebox.showerror("Lỗi Trích xuất", error or "Không có từ vựng nào được trích xuất.", parent=self)
            return
            
        # Import to GlossaryManager
        added_count = 0
        gm = self.translation_service.glossary_manager
        
        # Create category if missing
        if target_category not in gm.get_categories():
            gm.add_category(target_category)
            
        terms_dict = {}
        for term_obj in terms:
            en = term_obj.get('en', '').strip()
            vi = term_obj.get('vi', '').strip()
            if en and vi:
                 terms_dict[en] = vi
                 
        added_count = gm.bulk_add_terms(terms_dict, target_category)
                     
        messagebox.showinfo(
            "Hoàn tất 🪄", 
            f"Đã phân tích xong!\n\nLưu thành công {added_count}/{len(terms)} từ vựng vào danh mục '{target_category}'.\n(Các từ trùng/lỗi cấu trúc bị bỏ qua).\n\n💡 Vui lòng vào Cài đặt -> Từ Vựng để xem và tinh chỉnh lại.", 
            parent=self
        )

    def _translate_article(self, article, force_retranslate=False):
        """Handle translation trigger."""
        import threading
        
        # 1. Check API Key
        engine = self.settings_manager.get("translation_engine", "cloud")
        if engine == "cloud" and not self.translation_service.api_key:
             messagebox.showwarning("Thiếu API Key", "Vui lòng nhập API Key trong phần Cài đặt trước.", parent=self)
             return

        # Ask for confirmation
        if force_retranslate:
            if not messagebox.askyesno("Xác nhận", "Bài viết này đã có bản dịch. Bạn có chắc muốn DỊCH LẠI (bản cũ sẽ bị ghi đè)?", parent=self):
                return
        else:
            if not messagebox.askyesno("Xác nhận", f"Bắt đầu dịch bài viết này bằng {engine.upper()} API?", parent=self):
                return

        article_id = article['id']
        
        # 2. Get Content from DB
        content_text = self.db_manager.get_article_content(article_id)
        if not content_text:
            messagebox.showwarning("Lỗi", "Không tìm thấy nội dung bài viết trong cơ sở dữ liệu.")
            return
        
        # 3. Show Loading Popup
        self._translation_start_time = time.time()
        
        self.loading_win = ctk.CTkToplevel(self)
        self.loading_win.title("Đang dịch...")
        self.loading_win.geometry("420x200")
        self.loading_win.transient(self)
        self.loading_win.grab_set()
        self.loading_win.resizable(False, False)
        
        # Article name
        ctk.CTkLabel(
            self.loading_win, 
            text=f"📝 {article.get('subtitle', 'bài viết')[:40]}",
            font=("Segoe UI", 13, "bold"), text_color="#e0e0e0"
        ).pack(pady=(15, 2))
        
        # Big Timer Display
        self.timer_label = ctk.CTkLabel(
            self.loading_win, text="00:00",
            font=("Consolas", 32, "bold"), text_color="#4fc3f7"
        )
        self.timer_label.pack(pady=(5, 5))
        
        # Status label (chunk progress)
        self.progress_label = ctk.CTkLabel(
            self.loading_win, text="Chuẩn bị...",
            font=("Segoe UI", 11), text_color="gray"
        )
        self.progress_label.pack(pady=(0, 5))
        
        # Progress bar — starts in indeterminate (animated) mode
        # switches to determinate when we know there are multiple chunks
        self.progress_bar = ctk.CTkProgressBar(
            self.loading_win, mode="indeterminate",
            height=12, corner_radius=6,
            progress_color="#4fc3f7"
        )
        self.progress_bar.pack(pady=(0, 15), padx=30, fill="x")
        self.progress_bar.start()  # start indeterminate animation
        _progress_switched = [False]  # closure-safe mutable container
        
        # Start ticking the timer
        self._tick_translation_timer()
        
        # 4. Run Translation in Background Thread with progress
        def progress_callback(current, total, status):
            """Update progress on main thread."""
            def update():
                if hasattr(self, 'loading_win') and self.loading_win.winfo_exists():
                    if total > 1 and not _progress_switched[0]:
                        # Multiple chunks: switch to determinate mode
                        self.progress_bar.stop()
                        self.progress_bar.configure(mode="determinate")
                        _progress_switched[0] = True
                    
                    if total > 1:
                        pct = current / total
                        self.progress_bar.set(pct)
                        self.progress_label.configure(text=f"{status}  ({int(pct*100)}%)")
                    else:
                        # Single chunk: keep animated, just update status text
                        self.progress_label.configure(text=status)
            self.after(0, update)
        
        def worker():
            try:
                # Get settings
                chunk_size = self.settings_manager.get("chunk_size", 3000)
                chunk_delay = self.settings_manager.get("chunk_delay", 2.0)
                engine = self.settings_manager.get("translation_engine", "cloud")
                
                start_time = time.time()
                translation = self.translation_service.translate_text(
                    content_text,
                    chunk_size=chunk_size,
                    delay=chunk_delay,
                    progress_callback=progress_callback
                )
                translation_time = time.time() - start_time
                word_count = article.get('word_count', 0) or 0
                
                if translation:
                    update_dynamic_wpm(
                        self.settings_manager, engine,
                        word_count, translation_time
                    )
                
                self.after(0, lambda: self._on_translation_complete(article_id, translation))
            except Exception as e:
                print(f"[Translation Worker Error] {e}")
                self.after(0, lambda: self._on_translation_complete(article_id, None))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _tick_translation_timer(self):
        """Updates the elapsed timer label every second while loading_win exists."""
        if not hasattr(self, 'loading_win') or not self.loading_win.winfo_exists():
            return
        elapsed = time.time() - self._translation_start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")
        self.loading_win.after(1000, self._tick_translation_timer)
    
    def _on_translation_complete(self, article_id: int, translation: str):
        """Callback when translation is finished (success or fail)."""
        # Close loading popup
        if hasattr(self, 'loading_win') and self.loading_win.winfo_exists():
            self.loading_win.destroy()
        
        if translation:
            # Save to database
            self.db_manager.update_article_translation(article_id, translation, 'translated')
            messagebox.showinfo("Thành công", "Dịch thành công! Bản dịch đã được lưu.", parent=self)
            # Refresh the content list to show updated status
            self._render_content()
            # Refresh ETA label with updated chapter data
            self._refresh_eta()
        else:
            messagebox.showerror("Lỗi", "Dịch thất bại. Vui lòng kiểm tra API Key và thử lại.", parent=self)

    def _refresh_eta(self):
        """Recalculates and updates the ETA label with the latest chapter data."""
        if not self.winfo_exists() or not hasattr(self, 'lbl_eta') or not self.lbl_eta.winfo_exists():
            return
        fresh_data = self.db_manager.get_book_details(self.book_id)
        if not fresh_data:
            return
            
        engine = self.settings_manager.get("translation_engine", "cloud")
        wpm_key = f"{engine}_llm_wpm"
        default_wpm = 6000 if engine == "cloud" else 180
        wpm = int(self.settings_manager.get(wpm_key, default_wpm))
        
        chapters = fresh_data.get('chapters', [])
        eta_text = calculate_book_eta(chapters, wpm=wpm, engine=engine)
        self.lbl_eta.configure(text=f"⏱ Ước tính dịch: {eta_text}")


    def _transform_article(self, article, variant_type: str):
        """Handle variant transformation (website/facebook) from archive text."""
        import threading
        
        if not self.translation_service.api_key:
            messagebox.showwarning("Thiếu API Key", "Vui lòng nhập API Key trong phần Cài đặt trước.")
            return
        
        archive_text = article.get('translation_text', '')
        if not archive_text:
            messagebox.showwarning("Chưa có bản dịch", "Cần dịch lưu trữ trước khi chuyển thể.")
            return

        article_id = article['id']
        original_text = self.db_manager.get_article_content(article_id) or ''
        label_map = {'website': 'Website', 'facebook': 'Facebook'}
        label = label_map.get(variant_type, variant_type)

        # Loading popup
        self.loading_win = ctk.CTkToplevel(self)
        self.loading_win.title(f"Chuyển thể → {label}")
        self.loading_win.geometry("350x100")
        self.loading_win.transient(self)
        self.loading_win.grab_set()
        ctk.CTkLabel(
            self.loading_win, text=f"Đang tạo bản {label}...", 
            font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(25, 5))
        self.progress_bar = ctk.CTkProgressBar(self.loading_win, mode="indeterminate")
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_bar.start()

        def worker():
            result, err = self.translation_service.transform_text(archive_text, original_text, variant_type)
            self.after(0, lambda: self._on_transform_complete(article_id, variant_type, result, err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_transform_complete(self, article_id, variant_type, result, error):
        """Callback when variant transformation finishes."""
        if hasattr(self, 'loading_win') and self.loading_win.winfo_exists():
            self.loading_win.destroy()
        
        label_map = {'website': 'Website', 'facebook': 'Facebook'}
        label = label_map.get(variant_type, variant_type)
        
        if result:
            self.db_manager.update_article_variant(article_id, variant_type, result)
            messagebox.showinfo("Thành công", f"Bản {label} đã được tạo và lưu!", parent=self)
            self._render_content()
        else:
            messagebox.showerror("Lỗi", f"Chuyển thể {label} thất bại: {error}", parent=self)
        
    def _open_dual_view(self, article):
         """Opens the Dual View Editor."""
         # Fetch full content first
         content_text = self.db_manager.get_article_content(article['id'])
         full_article = article.copy()
         full_article['content_text'] = content_text
         
         editor = DualViewEditor(self, full_article, self._save_translation_update, self.db_manager)
         editor.grab_set()
         
    def _save_translation_update(self, article_id, new_text):
        """Callback to save edited translation."""
        self.db_manager.update_article_translation(article_id, new_text, 'translated')
        self._render_content()

    def _generate_and_open_webview(self):
        """Generates and opens the webview for this book."""
        try:
             # Generate folders
             output_dir = Path("user_data/webviews") / str(self.book_id)
             images_dir = output_dir / "images"
             images_dir.mkdir(parents=True, exist_ok=True)
             
             # Fetch full content & Copy Images
             full_chapters = []
             for chap_lite in self.chapters:
                 full_articles = []
                 for art_lite in chap_lite.get('articles', []):
                     # Fetch content text
                     art_id = art_lite['id']
                     content = self.db_manager.get_article_content(art_id)
                     trans = art_lite.get('translation_text', '')
                     
                     # Fetch and Copy Images
                     images = self.db_manager.get_article_images(art_id)
                     for img in images:
                         src_path = Path(img['path'])
                         if src_path.exists():
                             dest_path = images_dir / src_path.name
                             if not dest_path.exists():
                                 try:
                                     shutil.copy2(src_path, dest_path)
                                 except Exception as img_err:
                                     print(f"Error copying image {src_path}: {img_err}")
                     
                     full_articles.append({
                         'subtitle': art_lite.get('subtitle'),
                         'content_text': content,
                         'translation_text': trans
                     })
                 
                 full_chapters.append({
                     'title': chap_lite.get('title'),
                     'articles': full_articles
                 })
             
             # Generate
             # Output dir is already set above
             intro_title = self.title()
             
             index_path = webview_generator.generate_webview(
                 intro_title, "Author", full_chapters, output_dir
             )
             
             # Open
             webbrowser.open(index_path.resolve().as_uri())
             
        except Exception as e:
            messagebox.showerror("Lỗi Webview", f"Không thể tạo webview: {e}")
            print(e)
