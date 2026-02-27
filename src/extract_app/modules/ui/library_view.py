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
from pathlib import Path
from ...core import webview_generator
import os
import webbrowser
import shutil
import datetime
from .theme import Colors, Fonts, Spacing
from .editor_view import DualViewEditor
from .tooltip import ToolTip

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
        
        # Fixed card size
        self.configure(width=220, height=360)
        self.grid_propagate(False)
        self.pack_propagate(False)
        
        # Hover Effect Triggers
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Layout: Image (Top) -> Info (Bottom)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Image area
        self.grid_rowconfigure(1, weight=0) # Text area
        
        # 1. Cover Image
        self.cover_image = None
        if cover_path and Path(cover_path).exists():
            try:
                img = Image.open(cover_path)
                self.cover_image = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 160))
            except Exception as e:
                print(f"Error loading cover: {e}")
        
        if self.cover_image:
            self.lbl_cover = ctk.CTkLabel(self, text="", image=self.cover_image)
        else:
            self.lbl_cover = ctk.CTkLabel(
                self, text="📚\nNo Cover", 
                font=Fonts.H3,
                fg_color=Colors.BG_APP,
                text_color=Colors.TEXT_MUTED,
                corner_radius=10,
                width=120, height=160
            )
            
        self.lbl_cover.grid(row=0, column=0, pady=(Spacing.LG, Spacing.SM), padx=Spacing.LG)
        self._bind_click(self.lbl_cover)
        
        # 2. Info Frame
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(0, Spacing.MD))
        self.info_frame.grid_columnconfigure(0, weight=1)
        
        # Truncate logic for title (rough approx for 2 lines)
        display_title = full_title
        if len(display_title) > 42:
            display_title = display_title[:39] + "..."
            
        # Title
        self.title_label = ctk.CTkLabel(
            self.info_frame, text=display_title, font=Fonts.BODY_BOLD, 
            text_color=Colors.TEXT_PRIMARY,
            anchor="center", justify="center", wraplength=190
        )
        self.title_label.pack(fill="x", pady=(0, 2))
        self._bind_click(self.title_label)
        
        # Tooltip for full title
        if len(full_title) > 42:
             ToolTip(self.title_label, full_title)
        
        # Author & Year
        author_text = author
        if published_year:
             author_text = f"{author} • {published_year}"
             
        self.author_label = ctk.CTkLabel(
            self.info_frame, text=author_text, font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED
        )
        self.author_label.pack(fill="x", pady=(0, 2))
        self._bind_click(self.author_label)

        # Meta tags frame
        self.meta_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.meta_frame.pack(fill="x", pady=(0, Spacing.SM))
        
        if category:
            lbl_cat = ctk.CTkLabel(
                self.meta_frame, text=category, font=Fonts.TINY,
                fg_color=Colors.BG_APP, text_color=Colors.PRIMARY,
                corner_radius=4, padx=6, pady=2
            )
            lbl_cat.pack(side="top")

        # Delete Button (Pushed to bottom)
        self.btn_delete = ctk.CTkButton(
            self.info_frame, text="🗑 Xóa", width=60, height=24,
            fg_color="transparent", text_color=Colors.DANGER,
            hover_color=Colors.DANGER_HOVER,
            font=Fonts.TINY,
            command=self._handle_delete
        )
        self.btn_delete.pack(side="bottom", pady=4)

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
            # Chapter Header
            chap_title = chapter.get('title', 'Unknown Chapter')
            frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            frame.pack(fill="x", pady=Spacing.SM)
            
            ctk.CTkLabel(
                frame, text=chap_title, font=Fonts.H3, 
                text_color=Colors.TEXT_PRIMARY, anchor="w"
            ).pack(fill="x", pady=Spacing.SM)
            
            # Articles
            for article in chapter.get('articles', []):
                art_frame = ctk.CTkFrame(
                    self.list_frame, fg_color=Colors.BG_APP, 
                    corner_radius=Spacing.BUTTON_RADIUS
                )
                art_frame.pack(fill="x", pady=2, padx=Spacing.MD)
                
                status = article.get('status', 'new')
                is_translated = status == 'translated'
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
                is_leaf = article.get('is_leaf', 1)
                
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
                         # Website variant button
                         has_web = bool(article.get('website_text'))
                         web_fg = Colors.BG_CARD if has_web else "transparent"
                         ctk.CTkButton(
                             right_frame, text="🌐", width=32, height=26,
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
                             fg_color=fb_fg, border_width=1, border_color=Colors.WARNING,
                             text_color=Colors.WARNING, hover_color=Colors.BG_CARD_HOVER,
                             font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                             command=lambda a=article: self._transform_article(a, 'facebook')
                         ).pack(side="left", padx=2, pady=4)
                    else:
                         ctk.CTkButton(
                             right_frame, text="📥 Dịch Lưu trữ", width=110, height=26, 
                             fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY, hover_color=Colors.PRIMARY_HOVER,
                             font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                             command=lambda a=article: self._translate_article(a)
                         ).pack(side="left", padx=2, pady=4)
                else:
                    # Container articles
                    ctk.CTkLabel(
                        right_frame, text="(Mục lục)", 
                        text_color=Colors.TEXT_MUTED, font=Fonts.TINY
                    ).pack(side="left", padx=Spacing.MD, pady=2)
                     
    def _translate_article(self, article):
        """Handle translation trigger."""
        import threading
        
        # 1. Check API Key
        if not self.translation_service.api_key:
             messagebox.showwarning("Thiếu API Key", "Vui lòng nhập API Key trong phần Cài đặt trước.")
             return

        article_id = article['id']
        
        # 2. Get Content from DB
        content_text = self.db_manager.get_article_content(article_id)
        if not content_text:
            messagebox.showwarning("Lỗi", "Không tìm thấy nội dung bài viết trong cơ sở dữ liệu.")
            return
        
        # 3. Show Loading Popup
        self.loading_win = ctk.CTkToplevel(self)
        self.loading_win.title("Đang dịch...")
        self.loading_win.geometry("350x120")
        self.loading_win.transient(self)
        self.loading_win.grab_set()
        
        ctk.CTkLabel(self.loading_win, text=f"Đang dịch: {article.get('subtitle', 'bài viết')[:30]}...", font=("Segoe UI", 12)).pack(pady=(20, 5))
        
        self.progress_label = ctk.CTkLabel(self.loading_win, text="Chuẩn bị...", text_color="gray")
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.loading_win, mode="determinate")
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_bar.set(0)
        
        # 4. Run Translation in Background Thread with progress
        def progress_callback(current, total, status):
            """Update progress on main thread."""
            def update():
                if hasattr(self, 'loading_win') and self.loading_win.winfo_exists():
                    self.progress_label.configure(text=status)
                    if total > 0:
                        self.progress_bar.set(current / total)
            self.after(0, update)
        
        def worker():
            try:
                # Get settings
                chunk_size = self.settings_manager.get("chunk_size", 3000)
                chunk_delay = self.settings_manager.get("chunk_delay", 2.0)
                
                translation = self.translation_service.translate_text(
                    content_text,
                    chunk_size=chunk_size,
                    delay=chunk_delay,
                    progress_callback=progress_callback
                )
                self.after(0, lambda: self._on_translation_complete(article_id, translation))
            except Exception as e:
                print(f"[Translation Worker Error] {e}")
                self.after(0, lambda: self._on_translation_complete(article_id, None))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _on_translation_complete(self, article_id: int, translation: str):
        """Callback when translation is finished (success or fail)."""
        # Close loading popup
        if hasattr(self, 'loading_win') and self.loading_win.winfo_exists():
            self.loading_win.destroy()
        
        if translation:
            # Save to database
            self.db_manager.update_article_translation(article_id, translation, 'translated')
            messagebox.showinfo("Thành công", "Dịch thành công! Bản dịch đã được lưu.")
            # Refresh the content list to show updated status
            self._render_content()
        else:
            messagebox.showerror("Lỗi", "Dịch thất bại. Vui lòng kiểm tra API Key và thử lại.")

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
            messagebox.showinfo("Thành công", f"Bản {label} đã được tạo và lưu!")
            self._render_content()
        else:
            messagebox.showerror("Lỗi", f"Chuyển thể {label} thất bại: {error}")
        
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
