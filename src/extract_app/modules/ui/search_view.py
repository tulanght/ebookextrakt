# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/search_view.py
# Version: 1.0.0
# Author: Antigravity
# Description: Search UI for querying articles via FTS5.
# --------------------------------------------------------------------------------

import threading
import sqlite3
from typing import Any, Dict, List, Optional
import customtkinter as ctk
from .theme import Colors, Fonts, Spacing

class SearchView(ctk.CTkFrame):
    def __init__(self, master, db_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db_manager = db_manager
        
        # Grid layout: left (weight 2), right (weight 3)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        
        self._init_left_panel()
        self._init_right_panel()
        
    def _init_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(Spacing.LG, Spacing.MD), pady=Spacing.LG)
        
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(1, weight=1)
        
        # Search Bar Row
        search_bar_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        search_bar_frame.grid(row=0, column=0, sticky="ew", padx=Spacing.LG, pady=Spacing.LG)
        search_bar_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_search = ctk.CTkEntry(
            search_bar_frame, 
            placeholder_text="🔍 Tìm trong 91,521 articles...", 
            fg_color=Colors.BG_INPUT, 
            height=40
        )
        self.entry_search.grid(row=0, column=0, sticky="ew", padx=(0, Spacing.SM))
        self.entry_search.bind("<Return>", lambda event: self._on_search())
        
        self.option_category_var = ctk.StringVar(value="Tất cả")
        self.option_category = ctk.CTkSegmentedButton(
            search_bar_frame, 
            variable=self.option_category_var,
            values=["Tất cả", "animal", "plant", "overlap"]
        )
        self.option_category.grid(row=0, column=1, padx=(0, Spacing.SM))
        
        self.btn_search = ctk.CTkButton(
            search_bar_frame, 
            text="Tìm", 
            fg_color=Colors.PRIMARY, 
            width=80,
            command=self._on_search
        )
        self.btn_search.grid(row=0, column=2)
        
        # Results area
        self.results_scroll = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        self.results_scroll.grid(row=1, column=0, sticky="nsew", padx=Spacing.SM, pady=(0, Spacing.SM))
        self.results_scroll.grid_columnconfigure(0, weight=1)
        
        # State label
        self.lbl_status = ctk.CTkLabel(
            self.results_scroll, 
            text="Nhập từ khóa để tìm trong thư viện ebooks.", 
            text_color=Colors.TEXT_MUTED
        )
        self.lbl_status.grid(row=0, column=0, pady=Spacing.XL)
        
        self.result_cards = []
        self.active_card = None

    def _init_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(Spacing.MD, Spacing.LG), pady=Spacing.LG)
        
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(2, weight=1) # 0: empty state, 2: content area when shown
        
        self.lbl_empty_detail = ctk.CTkLabel(
            self.right_frame, 
            text="Chọn một kết quả để xem nội dung đầy đủ.", 
            text_color=Colors.TEXT_MUTED
        )
        self.lbl_empty_detail.grid(row=0, column=0, pady=Spacing.XL * 2)
        
        # Detail container (hidden by default)
        self.detail_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.detail_container.grid_columnconfigure(0, weight=1)
        self.detail_container.grid_rowconfigure(3, weight=1) # The textbox should expand
        
        # Header
        self.lbl_book_title = ctk.CTkLabel(
            self.detail_container, text="", font=Fonts.H3, text_color=Colors.TEXT_PRIMARY, anchor="w"
        )
        self.lbl_book_title.grid(row=0, column=0, sticky="ew", padx=Spacing.LG, pady=(Spacing.LG, 2))
        
        header_meta_frame = ctk.CTkFrame(self.detail_container, fg_color="transparent")
        header_meta_frame.grid(row=1, column=0, sticky="ew", padx=Spacing.LG, pady=(0, Spacing.MD))
        
        self.lbl_breadcrumb = ctk.CTkLabel(
            header_meta_frame, text="", text_color=Colors.TEXT_MUTED, anchor="w"
        )
        self.lbl_breadcrumb.pack(side="left", padx=(0, Spacing.SM))
        
        self.lbl_category_badge = ctk.CTkLabel(
            header_meta_frame, text="", fg_color=Colors.PRIMARY, text_color="white", corner_radius=4, padx=6
        )
        self.lbl_category_badge.pack(side="left")
        
        # Separator
        sep = ctk.CTkFrame(self.detail_container, height=1, fg_color=Colors.BORDER)
        sep.grid(row=2, column=0, sticky="ew", padx=Spacing.LG, pady=(0, Spacing.MD))
        
        # Textbox
        self.textbox_content = ctk.CTkTextbox(
            self.detail_container,
            fg_color=Colors.BG_INPUT,
            font=Fonts.CODE,
            wrap="word",
            state="disabled"
        )
        self.textbox_content.grid(row=3, column=0, sticky="nsew", padx=Spacing.LG, pady=(0, Spacing.LG))
        
        # Action Row
        action_frame = ctk.CTkFrame(self.detail_container, fg_color="transparent")
        action_frame.grid(row=4, column=0, sticky="ew", padx=Spacing.LG, pady=(0, Spacing.LG))
        
        self.btn_copy = ctk.CTkButton(
            action_frame,
            text="📋 Copy đoạn văn",
            command=self._on_copy
        )
        self.btn_copy.pack(side="right")
        
        self.current_passage_text = ""

    def _clear_results(self) -> None:
        for card in self.result_cards:
            card.destroy()
        self.result_cards.clear()
        self.active_card = None
        self.lbl_status.grid_forget()

    def _show_loading(self) -> None:
        self.lbl_status.configure(text="Đang tìm...")
        self.lbl_status.grid(row=0, column=0, pady=Spacing.XL)

    def _show_error(self, message: str) -> None:
        self._clear_results()
        self.lbl_status.configure(text=f"Lỗi: {message}")
        self.lbl_status.grid(row=0, column=0, pady=Spacing.XL)

    def _on_search(self) -> None:
        query: str = self.entry_search.get().strip()
        if not query:
            return

        category_label = self.option_category_var.get()
        category = None if category_label == "Tất cả" else category_label

        self._clear_results()
        self._show_loading()
        # Hide detail
        self.detail_container.grid_forget()
        self.lbl_empty_detail.grid(row=0, column=0, pady=Spacing.XL * 2)

        def worker():
            try:
                results = self.db_manager.search_content(
                    query=query,
                    site_category=category,
                    limit=20,
                    min_words=50
                )
                self.after(0, lambda: self._render_results(results, query))
            except sqlite3.Error as db_err:
                self.after(0, lambda err_msg=str(db_err): self._show_error(f"Lỗi Database: {err_msg}"))
            except Exception as system_err: # Bắt fallback nếu có lỗi logic Python
                self.after(0, lambda err_msg=str(system_err): self._show_error(f"Lỗi Hệ thống: {err_msg}"))

        threading.Thread(target=worker, daemon=True).start()

    def _render_results(self, results: List[Dict[str, Any]], query: str) -> None:
        self.lbl_status.grid_forget()
        
        if not results:
            self.lbl_status.configure(text=f"Không tìm thấy kết quả cho '{query}'.")
            self.lbl_status.grid(row=0, column=0, pady=Spacing.XL)
            return
            
        for idx, item in enumerate(results):
            card = self._create_result_card(item, idx)
            card.grid(row=idx, column=0, sticky="ew", pady=(0, Spacing.SM))
            self.result_cards.append(card)

    def _create_result_card(self, item: Dict[str, Any], index: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self.results_scroll, 
            fg_color="transparent", 
            border_width=1, 
            border_color=Colors.BORDER,
            corner_radius=Spacing.BUTTON_RADIUS,
            cursor="hand2"
        )
        card.grid_columnconfigure(0, weight=1)
        
        # Click handler
        def on_click(event: Any, current_card: ctk.CTkFrame = card, card_data: Dict[str, Any] = item) -> None:
            self._select_card(current_card, card_data)
            
        card.bind("<Button-1>", on_click)
        
        book_title = item.get("book_title", "Unknown")
        chapter_title = item.get("chapter_title", "")
        section_title = item.get("section_title", "")
        category = item.get("site_category", "none")
        snippet = item.get("snippet", "").replace("<b>", "").replace("</b>", "")
        
        breadcrumb = f"{chapter_title} › {section_title}" if section_title else chapter_title
        
        # Top row: Book Title
        lbl_title = ctk.CTkLabel(
            card, text=book_title, font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w",
            cursor="hand2"
        )
        lbl_title.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        lbl_title.bind("<Button-1>", on_click)
        
        # Middle row: Category badge + Breadcrumb
        meta_frame = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        meta_frame.grid(row=1, column=0, sticky="ew", padx=Spacing.MD, pady=(2, 2))
        meta_frame.bind("<Button-1>", on_click)
        
        if category == "animal":
            badge_color = Colors.SUCCESS
        elif category == "plant":
            badge_color = Colors.WARNING
        elif category == "overlap":
            badge_color = Colors.PRIMARY
        else:
            badge_color = Colors.TEXT_MUTED
            
        lbl_cat = ctk.CTkLabel(
            meta_frame, text=f" {category} ", fg_color=badge_color, text_color="white", 
            corner_radius=4, font=Fonts.TINY, cursor="hand2"
        )
        lbl_cat.pack(side="left")
        lbl_cat.bind("<Button-1>", on_click)
        
        lbl_bread = ctk.CTkLabel(
            meta_frame, text=breadcrumb, text_color=Colors.TEXT_MUTED, font=Fonts.TINY, cursor="hand2"
        )
        lbl_bread.pack(side="left", padx=(Spacing.SM, 0))
        lbl_bread.bind("<Button-1>", on_click)
        
        # Bottom row: Snippet
        snippet_text = snippet[:150] + "..." if len(snippet) > 150 else snippet
        lbl_snippet = ctk.CTkLabel(
            card, text=f'"{snippet_text}"', text_color=Colors.TEXT_MUTED, font=Fonts.TINY, 
            anchor="w", justify="left", cursor="hand2"
        )
        lbl_snippet.grid(row=2, column=0, sticky="ew", padx=Spacing.MD, pady=(0, Spacing.SM))
        lbl_snippet.bind("<Button-1>", on_click)
        
        return card

    def _select_card(self, card_widget: ctk.CTkFrame, item: Dict[str, Any]) -> None:
        if self.active_card:
            self.active_card.configure(border_color=Colors.BORDER)
        
        self.active_card = card_widget
        self.active_card.configure(border_color=Colors.PRIMARY)
        
        self.lbl_empty_detail.grid_forget()
        self.detail_container.grid(row=0, column=0, sticky="nsew")
        
        self.lbl_book_title.configure(text=item.get("book_title", "Unknown"))
        
        chapter_title = item.get("chapter_title", "")
        section_title = item.get("section_title", "")
        breadcrumb = f"{chapter_title} › {section_title}" if section_title else chapter_title
        self.lbl_breadcrumb.configure(text=breadcrumb)
        
        category = item.get("site_category", "none")
        if category == "animal":
            badge_color = Colors.SUCCESS
        elif category == "plant":
            badge_color = Colors.WARNING
        elif category == "overlap":
            badge_color = Colors.PRIMARY
        else:
            badge_color = Colors.TEXT_MUTED
            
        self.lbl_category_badge.configure(text=f" {category} ", fg_color=badge_color)
        
        passage_text = item.get("passage", "")
        self.current_passage_text = passage_text
        
        self.btn_copy.configure(text="📋 Copy đoạn văn")
        
        self.textbox_content.configure(state="normal")
        self.textbox_content.delete("0.0", "end")
        self.textbox_content.insert("0.0", passage_text)
        self.textbox_content.configure(state="disabled")

    def _on_copy(self) -> None:
        if self.current_passage_text:
            self.clipboard_clear()
            self.clipboard_append(self.current_passage_text)
            self.btn_copy.configure(text="✅ Đã copy")
            self.after(2000, lambda: self.btn_copy.configure(text="📋 Copy đoạn văn"))
