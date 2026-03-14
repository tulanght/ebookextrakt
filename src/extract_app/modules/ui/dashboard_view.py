# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/dashboard_view.py
# Version: 2.0.0
# Author: Antigravity
# Description: Dashboard/Welcome view with modern card-based layout (Dark Navy).
# --------------------------------------------------------------------------------

"""
Dashboard/Welcome view — Dark Navy style with modern Cards.
"""
from typing import Callable, List, Dict
from functools import partial
from pathlib import Path
import customtkinter as ctk
from .theme import Colors, Fonts, Spacing

class DashboardView(ctk.CTkFrame):
    """
    Home screen with modern card-based layout.
    Features: Welcome message, Import card, Recent files card.
    """
    def __init__(self, master, on_import: Callable, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_import = on_import
        
        # Main container with padding
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=Spacing.XL, pady=Spacing.XL)
        
        # === Header ===
        ctk.CTkLabel(
            self.container, text="Dashboard",
            font=Fonts.H1, text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(fill="x", pady=(0, Spacing.XS))
        
        ctk.CTkLabel(
            self.container, 
            text="Trích xuất nội dung Ebook mạnh mẽ & nhanh chóng",
            font=Fonts.BODY, text_color=Colors.TEXT_MUTED, anchor="w"
        ).pack(fill="x", pady=(0, Spacing.XL))

        # === Top Cards Row ===
        cards_row = ctk.CTkFrame(self.container, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, Spacing.LG))
        cards_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="card")

        # Card 1: Import
        self._create_stat_card(cards_row, "📥", "Import File", "PDF / EPUB", 
                               col=0, command=self.on_import, accent=Colors.PRIMARY)
        
        # Card 2: Placeholder for stats
        self.lbl_library_count = self._create_stat_card(cards_row, "📚", "Thư viện", "0 cuốn sách", col=1)
        
        # Card 3: Placeholder
        self.lbl_translated_count = self._create_stat_card(cards_row, "🌐", "Đã dịch", "0 bài viết", col=2, accent=Colors.SUCCESS)

        # === Recent Files Card ===
        recent_card = ctk.CTkFrame(
            self.container, fg_color=Colors.BG_CARD,
            corner_radius=Spacing.CARD_RADIUS,
            border_width=1, border_color=Colors.BORDER
        )
        recent_card.pack(fill="both", expand=True, pady=(0, Spacing.SM))
        
        # Card Header
        header_frame = ctk.CTkFrame(recent_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=Spacing.XL, pady=(Spacing.LG, Spacing.SM))
        
        ctk.CTkLabel(
            header_frame, text="📂  Mở gần đây", 
            font=Fonts.H3, text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left")
        
        # Card Body (scrollable list)
        self.history_frame = ctk.CTkScrollableFrame(
            recent_card, fg_color="transparent",
            scrollbar_button_color=Colors.BORDER,
            scrollbar_button_hover_color=Colors.TEXT_MUTED
        )
        self.history_frame.pack(fill="both", expand=True, padx=Spacing.LG, pady=(0, Spacing.LG))
        
        # Placeholder text
        self.no_history_label = ctk.CTkLabel(
            self.history_frame, text="Chưa có lịch sử mở file.", 
            text_color=Colors.TEXT_MUTED, font=Fonts.BODY
        )
        self.no_history_label.pack(pady=Spacing.XXL)

    def _create_stat_card(self, parent, icon, title, value, col=0, command=None, accent=None):
        """Create a small stat/action card."""
        card = ctk.CTkFrame(
            parent, fg_color=Colors.BG_CARD,
            corner_radius=Spacing.CARD_RADIUS,
            border_width=1, border_color=Colors.BORDER,
            height=100
        )
        card.grid(row=0, column=col, sticky="nsew", padx=Spacing.SM if col > 0 else (0, Spacing.SM), pady=0)
        card.grid_propagate(False)
        
        # Icon
        icon_color = accent or Colors.TEXT_MUTED
        ctk.CTkLabel(
            card, text=icon, font=("Segoe UI Emoji", 28), 
            text_color=icon_color
        ).pack(anchor="w", padx=Spacing.LG, pady=(Spacing.LG, Spacing.XS))
        
        # Title
        ctk.CTkLabel(
            card, text=title, font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(anchor="w", padx=Spacing.LG)
        
        # Value/Subtitle
        lbl_val = ctk.CTkLabel(
            card, text=value, font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED, anchor="w"
        )
        lbl_val.pack(anchor="w", padx=Spacing.LG, pady=(0, Spacing.SM))
        
        # Make the whole card clickable if command given
        if command:
            card.bind("<Button-1>", lambda e: command())
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e: command())
            # Hover effect
            card.bind("<Enter>", lambda e: card.configure(fg_color=Colors.BG_CARD_HOVER, border_color=Colors.BORDER_ACCENT))
            card.bind("<Leave>", lambda e: card.configure(fg_color=Colors.BG_CARD, border_color=Colors.BORDER))
            
        return lbl_val

    def update_stats(self, books_count: int, articles_count: int):
        """Update Dashboard stats counters."""
        if hasattr(self, 'lbl_library_count'):
            self.lbl_library_count.configure(text=f"{books_count} cuốn sách")
        if hasattr(self, 'lbl_translated_count'):
            self.lbl_translated_count.configure(text=f"{articles_count} bài viết đã dịch")

    def update_history(self, history_list: List[Dict], open_callback: Callable[[str], None]):
        """Update the Recent Files list."""
        for widget in self.history_frame.winfo_children():
            widget.destroy()
            
        if not history_list:
            lbl = ctk.CTkLabel(
                self.history_frame, text="Chưa có lịch sử mở file.", 
                text_color=Colors.TEXT_MUTED, font=Fonts.BODY
            )
            lbl.pack(pady=Spacing.XXL)
            return

        for item in history_list:
            filepath = item.get('filepath')
            title = item.get('title', Path(filepath).name)
            
            row = ctk.CTkFrame(self.history_frame, fg_color="transparent", height=38)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            
            btn = ctk.CTkButton(
                row, 
                text=f"   📄  {title}", 
                anchor="w", 
                fg_color="transparent",
                hover_color=Colors.BG_CARD_HOVER,
                text_color=Colors.TEXT_SECONDARY,
                font=Fonts.BODY,
                corner_radius=Spacing.BUTTON_RADIUS,
                command=partial(open_callback, filepath)
            )
            btn.pack(side="left", fill="both", expand=True)
