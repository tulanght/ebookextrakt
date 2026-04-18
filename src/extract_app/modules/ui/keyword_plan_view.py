# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/keyword_plan_view.py
# Version: 1.0.0
# Author: Antigravity
# Description: UI for managing Keyword Clusters (Phase 6).
# --------------------------------------------------------------------------------

import tkinter as tk
from typing import Dict, List
import customtkinter as ctk
import threading
from .theme import Colors, Fonts, Spacing
from .custom_dialog import ask_yes_no, show_info, show_error, show_warning

class KeywordPlanView(ctk.CTkFrame):
    """
    Layout: 
    - Left Panel: List of Clusters + "+ Create Cluster"
    - Right Panel: Detailed view of keywords in selected cluster
    """
    def __init__(self, master, db_manager, settings_manager, translation_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db_manager = db_manager
        self.settings_manager = settings_manager
        self.translation_service = translation_service
        
        self.clusters: List[Dict] = []
        self.active_cluster_id = None
        self.keywords: List[Dict] = []
        
        self.grid_columnconfigure(0, weight=1) # Left Panel 30%
        self.grid_columnconfigure(1, weight=3) # Right Panel 70%
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()
        
        self.refresh_clusters()

    def _build_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(Spacing.MD, Spacing.SM), pady=Spacing.MD)
        self.left_frame.grid_rowconfigure(1, weight=1)
        
        # Header Left
        header_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.MD)
        
        ctk.CTkLabel(header_frame, text="Keyword Clusters", font=Fonts.H3, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        ctk.CTkButton(
            header_frame, text="➕ Tạo mới", width=80, height=28,
            fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER,
            font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._open_create_cluster_modal
        ).pack(side="right")
        
        # Scrollable List
        self.cluster_list_frame = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        self.cluster_list_frame.grid(row=1, column=0, sticky="nsew", padx=Spacing.XS, pady=(0, Spacing.SM))

    def _build_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(Spacing.SM, Spacing.MD), pady=Spacing.MD)
        self.right_frame.grid_rowconfigure(2, weight=1)
        
        # Top Header
        self.right_header = ctk.CTkFrame(self.right_frame, fg_color="transparent", height=60)
        self.right_header.grid(row=0, column=0, sticky="ew", padx=Spacing.XL, pady=Spacing.MD)
        
        self.lbl_cluster_title = ctk.CTkLabel(self.right_header, text="Chọn một Cluster...", font=Fonts.H2, text_color=Colors.TEXT_PRIMARY)
        self.lbl_cluster_title.pack(side="left")
        
        self.btn_delete_cluster = ctk.CTkButton(
            self.right_header, text="🗑 Xóa", width=60, height=28,
            fg_color="transparent", border_width=1, border_color=Colors.DANGER, text_color=Colors.DANGER, hover_color=Colors.BG_CARD_HOVER,
            command=self._delete_active_cluster
        )
        self.btn_delete_cluster.pack(side="right")
        self.btn_delete_cluster.pack_forget() # Hide initially
        
        # Table Header
        self.table_header = ctk.CTkFrame(self.right_frame, fg_color=Colors.BG_CARD_HOVER, height=40)
        self.table_header.grid(row=1, column=0, sticky="ew", padx=Spacing.XL, pady=(Spacing.SM, 0))
        
        headers = [
            ("Từ khóa", 300, "w"),
            ("Loại nội dung", 150, "center"),
            ("Số chữ (Target)", 100, "center"),
            ("Trạng thái", 120, "center")
        ]
        
        for text, width, anchor in headers:
            ctk.CTkLabel(
                self.table_header, text=text, width=width,
                font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor=anchor
            ).pack(side="left", padx=4)
            
        # Table Content
        self.table_content = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        self.table_content.grid(row=2, column=0, sticky="nsew", padx=Spacing.MD, pady=(0, Spacing.MD))

    # ─────────────────────────────────────────────────────────────────
    # Cluster List Logic
    # ─────────────────────────────────────────────────────────────────

    def refresh_clusters(self):
        self.clusters = self.db_manager.get_keyword_clusters()
        
        for widget in self.cluster_list_frame.winfo_children():
            widget.destroy()
            
        if not self.clusters:
            ctk.CTkLabel(self.cluster_list_frame, text="Chưa có Topic Cluster nào.", font=Fonts.BODY, text_color=Colors.TEXT_MUTED).pack(pady=20)
            self.active_cluster_id = None
            self._render_active_cluster()
            return
            
        for cluster in self.clusters:
            self._create_cluster_card(cluster)

    def _create_cluster_card(self, cluster: Dict):
        is_active = cluster['id'] == self.active_cluster_id
        bg_col = Colors.BG_CARD_HOVER if is_active else "transparent"
        border_col = Colors.PRIMARY if is_active else Colors.BORDER
        
        card = ctk.CTkFrame(self.cluster_list_frame, fg_color=bg_col, border_width=1, border_color=border_col, corner_radius=Spacing.BUTTON_RADIUS)
        card.pack(fill="x", padx=Spacing.SM, pady=4)
        
        # Bind click event
        def on_click(event, cid=cluster['id']):
            self.active_cluster_id = cid
            self.refresh_clusters() # Update active visual
            self._render_active_cluster()
            
        card.bind("<Button-1>", on_click)
        
        lbl_name = ctk.CTkLabel(card, text=cluster['name'], font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w")
        lbl_name.pack(fill="x", padx=Spacing.SM, pady=(Spacing.SM, 0))
        lbl_name.bind("<Button-1>", on_click)
        
        lbl_desc = ctk.CTkLabel(card, text=cluster['description'][:30]+"..." if len(cluster['description'])>30 else cluster['description'], font=Fonts.TINY, text_color=Colors.TEXT_MUTED, anchor="w")
        lbl_desc.pack(fill="x", padx=Spacing.SM, pady=(0, Spacing.SM))
        lbl_desc.bind("<Button-1>", on_click)

    # ─────────────────────────────────────────────────────────────────
    # Active Cluster View Logic
    # ─────────────────────────────────────────────────────────────────

    def _render_active_cluster(self):
        for widget in self.table_content.winfo_children():
            widget.destroy()
            
        if not self.active_cluster_id:
            self.lbl_cluster_title.configure(text="Chọn một Cluster...")
            self.btn_delete_cluster.pack_forget()
            ctk.CTkLabel(self.table_content, text="Hãy chọn một Keyword Cluster bên trái hoặc tạo mới.", font=Fonts.BODY, text_color=Colors.TEXT_MUTED).pack(pady=50)
            return
            
        cluster = next((c for c in self.clusters if c['id'] == self.active_cluster_id), None)
        if not cluster:
            return
            
        self.lbl_cluster_title.configure(text=f"Cluster: {cluster['name']}")
        self.btn_delete_cluster.pack(side="right")
        
        self.keywords = self.db_manager.get_cluster_keywords(self.active_cluster_id)
        
        if not self.keywords:
            ctk.CTkLabel(self.table_content, text="Cluster rỗng.", font=Fonts.BODY, text_color=Colors.TEXT_MUTED).pack(pady=50)
            return
            
        for kw in self.keywords:
            self._create_keyword_row(kw)

    def _create_keyword_row(self, kw: Dict):
        row = ctk.CTkFrame(self.table_content, fg_color="transparent", height=40)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)
        
        bg_card = ctk.CTkFrame(row, fg_color=Colors.BG_INPUT, border_width=1, border_color=Colors.PRIMARY if kw['is_pillar'] else Colors.BORDER, corner_radius=Spacing.BUTTON_RADIUS)
        bg_card.pack(fill="both", expand=True, padx=Spacing.SM)
        bg_card.pack_propagate(False)
        
        # Keyword Label
        kw_text = f"⭐ {kw['keyword']}" if kw['is_pillar'] else f"↳ {kw['keyword']}"
        ctk.CTkLabel(bg_card, text=kw_text, font=Fonts.BODY_BOLD if kw['is_pillar'] else Fonts.BODY, text_color=Colors.PRIMARY if kw['is_pillar'] else Colors.TEXT_SECONDARY, anchor="w", width=300).pack(side="left", padx=(Spacing.SM, 4))
        
        # Content Type
        ctk.CTkLabel(bg_card, text=kw.get('content_type', ''), font=Fonts.SMALL, text_color=Colors.TEXT_MUTED, anchor="center", width=150).pack(side="left", padx=4)
        
        # Words Target
        ctk.CTkLabel(bg_card, text=str(kw.get('word_count_target', 0)), font=Fonts.SMALL, text_color=Colors.TEXT_MUTED, anchor="center", width=100).pack(side="left", padx=4)
        
        # Status Label
        status_map = {
            "pending": ("Chờ bài", Colors.WARNING),
            "linked": ("Đã liên kết", Colors.SUCCESS)
        }
        raw_status = kw.get('publish_status', 'pending')
        status_text, status_col = status_map.get(raw_status, ("Khác", Colors.TEXT_MUTED))
        
        if kw.get('article_id'):
            status_text = f"Đã có bài (#{kw.get('article_id')})"
            status_col = Colors.SUCCESS
            
        ctk.CTkLabel(bg_card, text=status_text, font=Fonts.SMALL, text_color=status_col, anchor="center", width=120).pack(side="left", padx=4)

    def _delete_active_cluster(self):
        if not self.active_cluster_id:
            return
        if ask_yes_no(self, "Xác nhận", "Bạn có chắc muốn xóa Cluster này cùng toàn bộ Keywords bên trong không?", is_danger=True):
            self.db_manager.delete_keyword_cluster(self.active_cluster_id)
            self.active_cluster_id = None
            self.refresh_clusters()

    # ─────────────────────────────────────────────────────────────────
    # AI Generation Logic
    # ─────────────────────────────────────────────────────────────────

    def _open_create_cluster_modal(self):
        if not self.translation_service.api_key:
            show_warning(self, "Thiếu API Key", "Vui lòng nhập Cloud API (Gemini) ở phần Cài đặt.")
            return
            
        modal = ctk.CTkToplevel(self)
        modal.title("Tạo Keyword Cluster Bằng AI")
        modal.geometry("500x330")
        modal.transient(self)
        modal.grab_set()
        modal.configure(fg_color=Colors.BG_APP)
        
        ctk.CTkLabel(modal, text="Nhập Từ khóa Pillar:", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(pady=(Spacing.MD, Spacing.XS), padx=Spacing.XL, anchor="w")
        
        entry_keyword = ctk.CTkEntry(modal, width=440, height=36, fg_color=Colors.BG_INPUT, border_color=Colors.BORDER)
        entry_keyword.pack(padx=Spacing.XL, pady=0)
        
        ctk.CTkLabel(modal, text="Ngữ cảnh/Niche/Website (Tùy chọn):", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(pady=(Spacing.SM, Spacing.XS), padx=Spacing.XL, anchor="w")
        
        entry_context = ctk.CTkEntry(modal, width=440, height=36, fg_color=Colors.BG_INPUT, border_color=Colors.BORDER)
        entry_context.pack(padx=Spacing.XL, pady=0)
        
        lbl_status = ctk.CTkLabel(modal, text="AI sẽ tự động sinh 8-10 từ khóa vệ tinh chuẩn SEO theo Topic Cluster.", font=Fonts.TINY, text_color=Colors.TEXT_MUTED)
        lbl_status.pack(padx=Spacing.XL, pady=5, anchor="w")
        
        def on_generate():
            kw = entry_keyword.get().strip()
            ctx = entry_context.get().strip()
            if not kw:
                return
            btn_gen.configure(state="disabled", text="Đang phân tích...")
            lbl_status.configure(text="Đang gửi lệnh tới Gemini AI...", text_color=Colors.WARNING)
            
            def worker():
                try:
                    cluster_payload, usage, err = self.translation_service.generate_keyword_cluster(kw, ctx)
                    if err:
                        self.after(0, lambda: lbl_status.configure(text=f"Lỗi: {err}", text_color=Colors.DANGER))
                        self.after(0, lambda: btn_gen.configure(state="normal", text="✨ Tạo bằng AI"))
                        return
                    
                    if cluster_payload:
                        # Save to DB
                        cid = self.db_manager.add_keyword_cluster(name=kw.title(), description=f"Cluster xoay quanh chủ đề: {kw}")
                        
                        # Add Pillar Keyword
                        self.db_manager.add_cluster_keyword(cid, kw, content_type="Pillar Content", is_pillar=True, word_count_target=2500)
                        
                        # Add Supporting Keywords
                        for node in cluster_payload:
                            child_kw = node.get("keyword", "Keyword")
                            ctype = node.get("content_type", "Bài viết")
                            wc = node.get("word_count_target", 1000)
                            self.db_manager.add_cluster_keyword(cid, child_kw, content_type=ctype, is_pillar=False, word_count_target=wc)
                            
                        self.after(0, lambda: self._on_cluster_generated(modal, cid))
                except Exception as e:
                    self.after(0, lambda: lbl_status.configure(text=f"Lỗi: {e}", text_color=Colors.DANGER))
                    self.after(0, lambda: btn_gen.configure(state="normal", text="✨ Tạo bằng AI"))
            
            threading.Thread(target=worker, daemon=True).start()

        btn_gen = ctk.CTkButton(modal, text="✨ Tạo bằng AI", fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY, hover_color=Colors.PRIMARY_HOVER, command=on_generate)
        btn_gen.pack(pady=Spacing.LG)
        
    def _on_cluster_generated(self, modal, cid):
        modal.destroy()
        self.active_cluster_id = cid
        self.refresh_clusters()
        show_info(self, "Hoàn tất", "Tạo Keyword Cluster thành công!")
