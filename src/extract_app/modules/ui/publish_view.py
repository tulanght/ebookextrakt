# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/publish_view.py
# Version: 1.0.0
# Author: Antigravity
# Description: The new CMS-style Publishing Pipeline view (Phase 3).
#              Lists all articles with tracking pipelines and fast edit options.
# --------------------------------------------------------------------------------

import tkinter as tk
from typing import Dict, List
import customtkinter as ctk

from .theme import Colors, Fonts, Spacing
from .custom_dialog import ask_yes_no, show_info

class PublishView(ctk.CTkFrame):
    """
    CMS-style table to manage articles through the Publishing Pipeline.
    """
    def __init__(self, master, db_manager, settings_manager, translation_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db_manager = db_manager
        self.settings_manager = settings_manager
        self.translation_service = translation_service
        
        self.articles: List[Dict] = []
        self.current_filter = "Tất cả"
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Scrollable frame takes remainder
        
        # 1. Top Header Action Bar
        self._build_top_bar()
        
        # 2. Filter Tabs Bar
        self._build_filter_tabs()
        
        # 3. Data Table Container
        self._build_data_table()
        
        self.refresh_list()

    def _build_top_bar(self):
        self.top_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, Spacing.MD))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        
        btn_add = ctk.CTkButton(
            self.top_frame, text="+ Thêm bài viết", width=120,
            fg_color=Colors.SUCCESS, hover_color=Colors.SUCCESS_HOVER,
            text_color="white", font=Fonts.BODY_BOLD,
            height=36, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._on_add_fake_article
        )
        btn_add.pack(side="left", padx=Spacing.MD, pady=Spacing.MD)
        
        self.entry_search = ctk.CTkEntry(
            self.top_frame, placeholder_text="🔍 Tìm kiếm bài viết...", 
            textvariable=self.search_var, width=350,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=36, corner_radius=Spacing.BUTTON_RADIUS
        )
        self.entry_search.pack(side="left", padx=(Spacing.SM, Spacing.MD), pady=Spacing.MD)
        
        self.btn_refresh = ctk.CTkButton(
            self.top_frame, text="🔄", width=40,
            fg_color=Colors.BG_CARD, border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY, hover_color=Colors.BG_CARD_HOVER,
            command=self.refresh_list,
            height=36, corner_radius=Spacing.BUTTON_RADIUS
        )
        self.btn_refresh.pack(side="right", padx=Spacing.XL)

    def _build_filter_tabs(self):
        self.tabs_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tabs_frame.grid(row=1, column=0, sticky="ew", padx=Spacing.MD, pady=(0, Spacing.MD))
        
        self.tab_buttons = {}
        tab_names = ["Tất cả", "Thiếu Thumb", "Thiếu Section", "Chờ duyệt", "Đã đăng", "Lỗi"]
        
        for name in tab_names:
            btn = ctk.CTkButton(
                self.tabs_frame, text=name, 
                width=0, height=30,
                fg_color="transparent", text_color=Colors.TEXT_MUTED,
                hover_color=Colors.BG_CARD_HOVER, corner_radius=Spacing.BUTTON_RADIUS,
                font=Fonts.SMALL,
                command=lambda n=name: self._set_filter(n)
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons[name] = btn
            
        # Optional Status counters
        self.lbl_stats = ctk.CTkLabel(
            self.tabs_frame, text="Tổng: 0 | Đã đăng: 0 | Chờ duyệt: 0",
            font=Fonts.TINY, text_color=Colors.TEXT_MUTED
        )
        self.lbl_stats.pack(side="right", padx=Spacing.MD)

    def _build_data_table(self):
        # Header Row
        self.header_frame = ctk.CTkFrame(self, fg_color=Colors.BG_CARD_HOVER, height=40, corner_radius=Spacing.BUTTON_RADIUS)
        self.header_frame.grid(row=2, column=0, sticky="ew", padx=Spacing.MD, pady=(0, 2))
        
        headers = [
            ("📝 Tiêu đề", 350, "w"),
            ("SEO", 50, "center"),
            ("Research", 80, "center"),
            ("Outline", 80, "center"),
            ("Nội dung", 90, "center"),
            ("Thumb", 70, "center"),
            ("Section", 70, "center"),
            ("Trạng thái", 100, "center"),
            ("Hành động", 100, "center")
        ]
        
        for text, width, anchor in headers:
            ctk.CTkLabel(
                self.header_frame, text=text, width=width,
                font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY,
                anchor=anchor
            ).pack(side="left", padx=4)
            
        # Scrollable Rows
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=Colors.BG_CARD,
            scrollbar_button_color=Colors.BORDER,
            scrollbar_button_hover_color=Colors.TEXT_MUTED,
            corner_radius=Spacing.CARD_RADIUS
        )
        self.scroll_frame.grid(row=3, column=0, sticky="nsew", padx=Spacing.MD, pady=(0, Spacing.XL))

    def _set_filter(self, filter_name: str):
        self.current_filter = filter_name
        for name, btn in self.tab_buttons.items():
            if name == filter_name:
                btn.configure(fg_color=Colors.BG_CARD, text_color=Colors.PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=Colors.TEXT_MUTED)
        self.refresh_list()

    def refresh_list(self):
        query = self.search_var.get().lower()
        # Mock load from DB for now until we optimize joining tables. 
        # Typically needs a custom SQL query in database.py: `get_publishing_pipeline_articles`
        conn = self.db_manager._get_connection()
        try:
            cursor = conn.cursor()
            # Fetch base articles with publish support features
            q = """
                SELECT a.id, a.subtitle, a.publish_status, a.seo_title, a.focus_keyword, a.word_count, a.translation_text
                FROM articles a 
                WHERE a.is_leaf = 1 AND a.status = 'translated'
            """
            cursor.execute(q)
            all_rows = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
            
        # Counts for tabs
        counts = {
            "Tất cả": len(all_rows),
            "Thiếu Thumb": 0,    # Mocked data handling below
            "Thiếu Section": 0,  # Mocked data handling below
            "Chờ duyệt": sum(1 for r in all_rows if r.get('publish_status') in ["ready", "translated", "optimized"]),
            "Đã đăng": sum(1 for r in all_rows if r.get('publish_status') == "published"),
            "Lỗi": sum(1 for r in all_rows if r.get('publish_status') == "error")
        }

        self.articles = []
        for row in all_rows:
            if query and query not in row.get('subtitle', '').lower() and query not in row.get('focus_keyword', '').lower() and query not in row.get('seo_title', '').lower():
                continue
            
            status = row.get('publish_status', 'translated')
            
            # Simple mock property for layout purposes (in real app, check image count/section count)
            missing_thumb = False 
            missing_section = False
            
            if missing_thumb: counts["Thiếu Thumb"] += 1
            if missing_section: counts["Thiếu Section"] += 1

            if self.current_filter == "Tất cả":
                self.articles.append(row)
            elif self.current_filter == "Đã đăng" and status == "published":
                self.articles.append(row)
            elif self.current_filter == "Chờ duyệt" and status in ["ready", "translated", "optimized"]:
                self.articles.append(row)
            elif self.current_filter == "Lỗi" and status == "error":
                self.articles.append(row)
            elif self.current_filter == "Thiếu Thumb" and missing_thumb:
                self.articles.append(row)
            elif self.current_filter == "Thiếu Section" and missing_section:
                self.articles.append(row)
            # Default fallback for unhandled filters is empty to avoid appending irrelevant rows
                
        # Update tab texts with counts
        for name, btn in self.tab_buttons.items():
            count = counts.get(name, 0)
            btn.configure(text=f"{name} ({count})")

        self._update_stats_label(all_rows)
        self._render_table_rows()

    def _update_stats_label(self, all_rows):
        total = len(all_rows)
        published = sum(1 for r in all_rows if r.get('publish_status') == 'published')
        pending = sum(1 for r in all_rows if r.get('publish_status') in ['ready', 'translated', 'optimized'])
        self.lbl_stats.configure(text=f"Tổng: {total} | Đã đăng: {published} | Chờ duyệt: {pending}")

    def _render_table_rows(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.articles:
            ctk.CTkLabel(
                self.scroll_frame, text="Không có bài viết nào thỏa điều kiện.",
                text_color=Colors.TEXT_MUTED, font=Fonts.BODY
            ).pack(pady=50)
            return

        for idx, article in enumerate(self.articles):
            self._create_row(article, idx)
            
    def _create_row(self, article, index):
        bg_color = Colors.BG_APP if index % 2 == 0 else "transparent"
        row = ctk.CTkFrame(self.scroll_frame, fg_color=bg_color, height=50, corner_radius=0)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        # Tiêu đề
        title_frame = ctk.CTkFrame(row, width=350, fg_color="transparent")
        title_frame.pack(side="left", padx=4, fill="y")
        title_frame.pack_propagate(False)
        
        # Display SEO Title if available, otherwise fallback to subtitle
        seo_title = article.get('seo_title')
        subtitle = article.get('subtitle', 'No Title')
        title_text = seo_title if seo_title else subtitle
        
        keyword = article.get('focus_keyword', '')
        
        ctk.CTkLabel(
            title_frame, text=title_text[:45] + ('...' if len(title_text) > 45 else ''),
            font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="top", anchor="w", pady=(8, 0))
        
        if keyword:
            ctk.CTkLabel(
                title_frame, text=keyword, font=Fonts.TINY, text_color=Colors.TEXT_MUTED, anchor="w"
            ).pack(side="top", anchor="w")

        # SEO Indicator Column
        has_seo = bool(seo_title and keyword)
        seo_color = Colors.SUCCESS if has_seo else Colors.TEXT_MUTED
        ctk.CTkLabel(
            row, text="✓" if has_seo else "—", width=50,
            font=Fonts.SMALL, text_color=seo_color, anchor="center"
        ).pack(side="left", padx=4)

        # Mock Progress Status (Research -> Outline -> Noidung -> Thumb -> Section)
        stages = [
            ("Research", True, 80),
            ("Outline", bool(article.get('focus_keyword')), 80),
            ("Nội dung", bool(article.get('translation_text')), 90),
            ("Thumb", False, 70),
            ("Section", False, 70)
        ]
        
        for name, done, width in stages:
            color = Colors.SUCCESS if done else Colors.TEXT_MUTED
            icon = "✓" if done else "—"
            if name == "Nội dung" and done:
                words = article.get('word_count', 0)
                icon = f"✓ {words//1000}k" if words > 1000 else f"✓ {words}"
                
            ctk.CTkLabel(
                row, text=icon, width=width,
                font=Fonts.SMALL, text_color=color, anchor="center"
            ).pack(side="left", padx=4)
            
        # Trạng Thái Publish
        status_raw = article.get('publish_status', 'translated')
        status_map = {
            "translated": ("Chờ duyệt", Colors.TEXT_MUTED),
            "optimized": ("Sẵn sàng", Colors.PRIMARY),
            "published": ("Đã đăng", Colors.SUCCESS),
            "error": ("Lỗi", Colors.DANGER)
        }
        status_text, status_color = status_map.get(status_raw, ("Khác", Colors.TEXT_MUTED))
        
        ctk.CTkLabel(
            row, text=status_text, width=100,
            font=Fonts.SMALL, text_color=status_color, anchor="center"
        ).pack(side="left", padx=4)

        # Actions
        actions_frame = ctk.CTkFrame(row, width=100, fg_color="transparent")
        actions_frame.pack(side="left", padx=4)
        actions_frame.pack_propagate(False)
        
        ctk.CTkButton(
            actions_frame, text="👁", width=30, height=30,
            fg_color="transparent", text_color=Colors.TEXT_MUTED, hover_color=Colors.BG_CARD_HOVER,
            command=lambda a=article: self._open_article_detail(a)
        ).pack(side="left", padx=2, pady=10)

    def _on_search_change(self, *args):
        self.refresh_list()
        
    def _on_add_fake_article(self):
        show_info(self, "Tạo bài viết", "Mở modal tạo bài viết trắng (Tự động liên kết mồ côi). Tính năng đang phát triển lúc cấu trúc keyword.")
        
    def _open_article_detail(self, article):
        # We will build PublishPipelineDetail Window here later
        show_info(self, "Chi tiết", f"Mở chi tiết bài viết: {article.get('subtitle')}")
