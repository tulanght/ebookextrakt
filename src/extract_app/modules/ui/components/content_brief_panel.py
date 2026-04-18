# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/components/content_brief_panel.py
# Version: 1.0.0
# Author: Antigravity
# Description: Generates and displays an AI Content Brief for SEO. Phase 5.
# --------------------------------------------------------------------------------

import json
import threading
import tkinter as tk
import customtkinter as ctk
from src.extract_app.modules.ui.theme import Colors, Fonts, Spacing

class ContentBriefPanel(ctk.CTkFrame):
    """
    Panel that fetches a Content Brief from Gemini and displays it in a clean grid.
    """
    def __init__(self, master, db_manager, translation_service, article_data: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db_manager = db_manager
        self.translation_service = translation_service
        self.article_data = article_data
        self.article_id = article_data.get('id', -1)
        
        self.brief_data = {}
        self.last_usage = None
        saved_brief = self.article_data.get('content_brief', '')
        if saved_brief:
            try:
                self.brief_data = json.loads(saved_brief)
            except Exception:
                pass
                
        self._build_ui()

    def _build_ui(self):
        # 1. Header Toolbar
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.header.pack(fill="x", pady=(0, Spacing.MD))
        
        ctk.CTkLabel(
            self.header, text="SEO Content Brief (AI Generated)", 
            font=Fonts.H3, text_color=Colors.TEXT_PRIMARY
        ).pack(side="left")
        
        self.btn_generate = ctk.CTkButton(
            self.header, text="✨ Phân tích AI", 
            width=120, height=32,
            fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER,
            command=self._generate_brief
        )
        self.btn_generate.pack(side="right")
        
        # Status Label & Token Display
        status_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        status_frame.pack(side="right", fill="y", padx=Spacing.MD)
        
        self.lbl_tokens = ctk.CTkLabel(status_frame, text="", font=Fonts.TINY, text_color=Colors.SUCCESS)
        self.lbl_tokens.pack(side="top", anchor="e")
        self.lbl_status = ctk.CTkLabel(status_frame, text="", font=Fonts.SMALL, text_color=Colors.TEXT_MUTED)
        self.lbl_status.pack(side="top", anchor="e")
        
        # 2. Scrollable Display Area
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS)
        self.scroll_area.pack(fill="both", expand=True)
        
        self._render_brief()

    def _render_brief(self):
        # Clear existing
        for widget in self.scroll_area.winfo_children():
            widget.destroy()
            
        if not self.brief_data:
            ctk.CTkLabel(
                self.scroll_area, text="Chưa có Content Brief cho bài viết này.\nNhấn 'Phân tích AI' để tạo.",
                font=Fonts.BODY, text_color=Colors.TEXT_MUTED, justify="center"
            ).pack(pady=40, expand=True)
            return
            
        # Search Intent & Audience
        row1 = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        row1.pack(fill="x", pady=(Spacing.SM, Spacing.MD))
        
        self._create_card(row1, "🎯 Search Intent", self.brief_data.get("search_intent", "")).pack(side="left", fill="x", expand=True, padx=(0, Spacing.SM))
        self._create_card(row1, "👥 Target Audience", self.brief_data.get("target_audience", "")).pack(side="left", fill="x", expand=True, padx=(Spacing.SM, 0))
        
        # Content Type & LSI
        row2 = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        row2.pack(fill="x", pady=(0, Spacing.MD))
        
        self._create_card(row2, "📄 Content Type", self.brief_data.get("content_type", "")).pack(side="left", fill="x", expand=True, padx=(0, Spacing.SM))
        
        lsi_list = self.brief_data.get("lsi_keywords", [])
        lsi_card = self._create_card(row2, "🔑 LSI Keywords", "")
        lsi_card.pack(side="left", fill="x", expand=True, padx=(Spacing.SM, 0))
        
        lsi_container = ctk.CTkFrame(lsi_card, fg_color="transparent")
        lsi_container.pack(fill="x", padx=Spacing.SM, pady=(0, Spacing.SM))
        
        for keyword in lsi_list:
             ctk.CTkLabel(
                 lsi_container, text=keyword,
                 fg_color=Colors.BG_APP, text_color=Colors.TEXT_PRIMARY,
                 corner_radius=12, padx=8, pady=2, font=Fonts.TINY
             ).pack(side="left", padx=(0, 4), pady=2)
        
        # Outline
        outline = self.brief_data.get("outline", [])
        if outline:
            outline_card = ctk.CTkFrame(self.scroll_area, fg_color=Colors.BG_INPUT, corner_radius=Spacing.BUTTON_RADIUS, border_width=1, border_color=Colors.BORDER)
            outline_card.pack(fill="x", pady=(0, Spacing.MD))
            
            out_header = ctk.CTkFrame(outline_card, fg_color="transparent")
            out_header.pack(fill="x", padx=Spacing.SM, pady=(Spacing.SM, 2))
            
            ctk.CTkLabel(out_header, text="📑 Outline (Dàn ý chính)", font=Fonts.BODY_BOLD, text_color=Colors.PRIMARY).pack(side="left")
            
            outline_text = "\n".join([f"• {item}" for item in outline])
            
            def copy_outline():
                self.clipboard_clear()
                self.clipboard_append(outline_text)
                self.update()
                
            ctk.CTkButton(
                out_header, text="📋 Copy Outline", width=100, height=24,
                font=Fonts.TINY, fg_color=Colors.BG_CARD, hover_color=Colors.BG_CARD_HOVER,
                text_color=Colors.TEXT_PRIMARY, command=copy_outline
            ).pack(side="right")
            
            ctk.CTkLabel(
                outline_card, text=outline_text, justify="left", 
                anchor="w", text_color=Colors.TEXT_SECONDARY, font=Fonts.BODY
            ).pack(fill="x", padx=Spacing.SM, pady=(0, Spacing.SM))
            
        # FAQs
        faqs = self.brief_data.get("faqs", [])
        if faqs:
            faq_card = self._create_card(self.scroll_area, "❓ Frequently Asked Questions (FAQs)", "")
            faq_card.pack(fill="x", pady=(0, Spacing.SM))
            
            for faq in faqs:
                q = faq.get("question", "")
                a = faq.get("answer", "")
                
                # Structured FAQ items
                item_frame = ctk.CTkFrame(faq_card, fg_color=Colors.BG_APP, corner_radius=8)
                item_frame.pack(fill="x", padx=Spacing.SM, pady=(Spacing.SM, 2))
                
                ctk.CTkLabel(item_frame, text=f"Q: {q}", font=Fonts.BODY_BOLD, text_color=Colors.WARNING, justify="left", anchor="w", wraplength=700).pack(fill="x", padx=Spacing.SM, pady=(Spacing.SM, 2))
                ctk.CTkLabel(item_frame, text=f"A: {a}", font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY, justify="left", anchor="w", wraplength=700).pack(fill="x", padx=Spacing.SM, pady=(0, Spacing.SM))

    def _create_card(self, parent, title, text):
        card = ctk.CTkFrame(parent, fg_color=Colors.BG_INPUT, corner_radius=Spacing.BUTTON_RADIUS, border_width=1, border_color=Colors.BORDER)
        ctk.CTkLabel(card, text=title, font=Fonts.BODY_BOLD, text_color=Colors.PRIMARY).pack(anchor="w", padx=Spacing.SM, pady=(Spacing.SM, 2))
        if text:
            ctk.CTkLabel(card, text=text, font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY, justify="left", anchor="w", wraplength=350).pack(fill="x", padx=Spacing.SM, pady=(0, Spacing.SM))
        return card

    def _generate_brief(self):
        text_source = self.article_data.get('content_text')
        if not text_source:
             self.lbl_status.configure(text="Lỗi: Bài viết không có nội dung.", text_color=Colors.DANGER)
             return
             
        self.btn_generate.configure(state="disabled", text="Đang phân tích...")
        self.lbl_status.configure(text="Đang gửi yêu cầu đến Gemini AI...", text_color=Colors.WARNING)
        
        def worker():
            try:
                # Truncate text context slightly if necessary, Gemini 1.5 flash handles 1M easily though
                brief, usage, err = self.translation_service.generate_content_brief(text_source)
                
                if err:
                    self.lbl_status.configure(text=f"Lỗi: {err}", text_color=Colors.DANGER)
                    
                    # Create an error card to display what went wrong
                    self.brief_data = {}
                    self.after(0, self._render_brief)
                    error_card = self._create_card(self.scroll_area, "❌ Lỗi khi phân tích AI", err)
                    error_card.pack(fill="x", pady=40, padx=40)
                    
                elif brief:
                    self.brief_data = brief
                    # Save to DB
                    brief_json = json.dumps(brief, ensure_ascii=False)
                    if self.db_manager and self.article_id != -1:
                        self.db_manager.update_article_brief(self.article_id, brief_json)
                        # Optional: Log Usage
                        self.db_manager.log_api_usage(
                            self.article_id, "content_brief", "cloud_gemini", 
                            usage.get("in", 0), usage.get("out", 0), 0.0
                        )
                    
                    self.last_usage = usage
                    # Update UI
                    self.after(0, self._render_brief)
                    self.lbl_status.configure(text="✅ Tạo Content Brief thành công!", text_color=Colors.SUCCESS)
                    
                    if self.last_usage:
                        cost = (usage.get('in', 0) * 0.075 / 1000000) + (usage.get('out', 0) * 0.3 / 1000000)
                        self.lbl_tokens.configure(text=f"Tokens: {usage.get('in', 0)} in / {usage.get('out', 0)} out (${cost:.5f})")
                        
            except Exception as e:
                self.lbl_status.configure(text="Lỗi phần mềm nội bộ (UI/Thread)", text_color=Colors.DANGER)
                
                self.brief_data = {}
                self.after(0, self._render_brief)
                error_card = self._create_card(self.scroll_area, "❌ Exception", str(e))
                error_card.pack(fill="x", pady=40, padx=40)
                
            finally:
                self.btn_generate.configure(state="normal", text="✨ Phân tích AI")
                
        threading.Thread(target=worker, daemon=True).start()
