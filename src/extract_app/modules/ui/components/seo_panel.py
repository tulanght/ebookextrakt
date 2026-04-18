# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/components/seo_panel.py
# Version: 1.0.0
# Author: Antigravity
# Description: Real-time UI Panel for SEO Title & Meta Description editing.
#              Simulates a Google SERP snippet. Phase 4 Component.
# --------------------------------------------------------------------------------

import tkinter as tk
import customtkinter as ctk
from src.extract_app.modules.ui.theme import Colors, Fonts, Spacing
from src.extract_app.modules.ui.tooltip import ToolTip

class SeoPanel(ctk.CTkFrame):
    """
    Panel providing inputs for SEO metadata and a live Google SERP preview.
    """
    def __init__(self, master, db_manager=None, article_data: dict = None, settings_manager=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db_manager = db_manager
        self.settings_manager = settings_manager
        self.article_data = article_data or {}
        
        self.article_id = self.article_data.get('id', -1)
        self.seo_title = tk.StringVar(value=self.article_data.get('seo_title') or "")
        self.meta_desc = tk.StringVar(value=self.article_data.get('meta_description') or "")
        self.focus_kw = tk.StringVar(value=self.article_data.get('focus_keyword') or "")
        
        self.seo_title.trace("w", self._on_input_change)
        self.meta_desc.trace("w", self._on_input_change)
        self.focus_kw.trace("w", self._on_input_change)
        
        self._build_ui()
        self._update_preview()

    def _build_ui(self):
        # 1. Editors
        editor_frame = ctk.CTkFrame(self, fg_color="transparent")
        editor_frame.pack(side="left", fill="both", expand=True, padx=(0, Spacing.MD))
        
        # Focus Keyword
        ctk.CTkLabel(
            editor_frame, text="Từ khóa chính (Focus Keyword)", 
            font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 2))
        
        self.entry_kw = ctk.CTkEntry(
            editor_frame, textvariable=self.focus_kw, height=36,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY, corner_radius=Spacing.BUTTON_RADIUS
        )
        self.entry_kw.pack(fill="x", pady=(0, Spacing.MD))
        
        # Title
        title_hdr = ctk.CTkFrame(editor_frame, fg_color="transparent")
        title_hdr.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(title_hdr, text="SEO Title", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.lbl_title_count = ctk.CTkLabel(title_hdr, text="0/60", font=Fonts.TINY, text_color=Colors.TEXT_MUTED)
        self.lbl_title_count.pack(side="right")
        
        self.entry_title = ctk.CTkEntry(
            editor_frame, textvariable=self.seo_title, height=36,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY, corner_radius=Spacing.BUTTON_RADIUS
        )
        self.entry_title.pack(fill="x", pady=(0, Spacing.MD))
        
        # Meta Description
        desc_hdr = ctk.CTkFrame(editor_frame, fg_color="transparent")
        desc_hdr.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(desc_hdr, text="Meta Description", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.lbl_desc_count = ctk.CTkLabel(desc_hdr, text="0/160", font=Fonts.TINY, text_color=Colors.TEXT_MUTED)
        self.lbl_desc_count.pack(side="right")
        
        self.txt_desc = ctk.CTkTextbox(
            editor_frame, height=80, wrap="word",
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, border_width=1,
            text_color=Colors.TEXT_PRIMARY, corner_radius=Spacing.BUTTON_RADIUS,
            font=Fonts.BODY
        )
        self.txt_desc.pack(fill="x", pady=(0, Spacing.MD))
        if self.meta_desc.get():
            self.txt_desc.insert("1.0", self.meta_desc.get())
            
        self.txt_desc.bind("<KeyRelease>", self._on_txtbox_change)
        
        # Save Button
        self.btn_save = ctk.CTkButton(
            editor_frame, text="💾 Lưu SEO", command=self._save_seo,
            width=120, height=36,
            fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY,
            hover_color=Colors.PRIMARY_HOVER, corner_radius=Spacing.BUTTON_RADIUS
        )
        self.btn_save.pack(anchor="w", pady=(Spacing.SM, 0))
        
        # 2. Preview SERP
        SERP_WIDTH = 420
        preview_container = ctk.CTkFrame(self, fg_color="transparent", width=SERP_WIDTH)
        preview_container.pack(side="right", fill="y")
        preview_container.pack_propagate(False)
        
        ctk.CTkLabel(
            preview_container, text="Google SERP Preview", 
            font=Fonts.BODY_BOLD, text_color=Colors.TEXT_MUTED
        ).pack(anchor="w", pady=(0, Spacing.SM))
        
        self.preview_card = ctk.CTkFrame(
            preview_container, fg_color="#fff", corner_radius=12,
            width=SERP_WIDTH, height=180
        )
        self.preview_card.pack(fill="x")
        self.preview_card.pack_propagate(False)
        
        # Emulate Google SERP Look
        # URL line
        url_frame = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        url_frame.pack(fill="x", padx=15, pady=(15, 2))
        
        domain = self.settings_manager.get("website_domain", "www.your-website.com") if self.settings_manager else "www.your-website.com"
        
        self.prev_url = ctk.CTkLabel(
            url_frame, text=f"{domain} › article-slug", 
            font=("Arial", 11), text_color="#1a0dab" # Google green/blue-ish URL
        )
        self.prev_url.pack(side="left")
        
        # Blue Title Link
        self.prev_title = ctk.CTkLabel(
            self.preview_card, text="SEO Title Preview", 
            font=("Arial", 18), text_color="#1a0dab", # Google Blue Link
            anchor="w", justify="left", wraplength=SERP_WIDTH - 30
        )
        self.prev_title.pack(fill="x", padx=15, pady=(2, 2))
        
        # Meta description snippet
        self.prev_desc = ctk.CTkLabel(
            self.preview_card, text="Meta description goes here...", 
            font=("Arial", 13), text_color="#4d5156", # Google dark gray text
            anchor="nw", justify="left", wraplength=SERP_WIDTH - 30, height=50
        )
        self.prev_desc.pack(fill="both", expand=True, padx=15, pady=(2, 10))

    def _on_txtbox_change(self, event=None):
        self.meta_desc.set(self.txt_desc.get("1.0", "end-1c").replace("\n", " "))
        self._update_preview()

    def _on_input_change(self, *args):
        self._update_preview()

    def _generate_slug(self, text: str) -> str:
        """Helper to generate a basic slug from title."""
        import re, unicodedata
        if not text:
            return "article-slug"
        # Normalize to ASCII
        s = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        s = s.lower().strip()
        # Replace non-alphanumeric with hyphen
        s = re.sub(r'[\W_]+', '-', s)
        # Collapse multiple hyphens
        s = re.sub(r'-+', '-', s)
        return s.strip('-') or "article-slug"
        
    def _update_preview(self):
        t_len = len(self.seo_title.get())
        d_len = len(self.meta_desc.get())
        k_len = len(self.focus_kw.get().strip())
        
        # Toggle save button
        if t_len == 0 and d_len == 0 and k_len == 0:
            self.btn_save.configure(state="disabled", text_color=Colors.TEXT_MUTED, fg_color=Colors.BG_CARD)
        else:
            self.btn_save.configure(state="normal", text_color=Colors.TEXT_PRIMARY, fg_color=Colors.PRIMARY)

        # Counters
        self.lbl_title_count.configure(
            text=f"{t_len}/60", 
            text_color=Colors.DANGER if t_len > 60 else (Colors.SUCCESS if 40 <= t_len <= 60 else Colors.TEXT_MUTED)
        )
        self.lbl_desc_count.configure(
            text=f"{d_len}/160", 
            text_color=Colors.DANGER if d_len > 160 else (Colors.SUCCESS if 120 <= d_len <= 160 else Colors.TEXT_MUTED)
        )
        
        # SERP Text
        display_title = self.seo_title.get() or "Nhập SEO Title để xem trước tiêu đề"
        if len(display_title) > 65:
            display_title = display_title[:62] + "..."
            
        display_desc = self.meta_desc.get() or "Nhập Meta description để xem trước mô tả trên Google Tìm kiếm..."
        if len(display_desc) > 160:
            display_desc = display_desc[:157] + "..."
            
        self.prev_title.configure(text=display_title)
        self.prev_desc.configure(text=display_desc)
        
        # URL Slug
        domain = self.settings_manager.get("website_domain", "www.your-website.com") if self.settings_manager else "www.your-website.com"
        slug = self._generate_slug(self.seo_title.get() or "article-slug")
        self.prev_url.configure(text=f"{domain} › {slug}")

    def _save_seo(self):
        title = self.seo_title.get().strip()
        desc = self.meta_desc.get().strip()
        kw = self.focus_kw.get().strip()
        
        if self.db_manager and self.article_id != -1:
            try:
                self.db_manager.update_article_seo(self.article_id, title, desc, kw)
                from tkinter import messagebox
                # Quick small tooltip instead of alert box
                btn_save = self.winfo_children()[0].winfo_children()[-1]
                t = ToolTip(btn_save, "Lưu thành công!")
                t.show()
                self.after(2000, t.hidetip)
            except Exception as e:
                print(f"Error saving SEO: {e}")
