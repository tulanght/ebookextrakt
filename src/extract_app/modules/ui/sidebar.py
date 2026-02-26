# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/sidebar.py
# Version: 2.0.0
# Author: Antigravity
# Description: Modern Dark Navy sidebar navigation component.
# --------------------------------------------------------------------------------

from typing import Callable, Optional
import customtkinter as ctk
from .theme import Colors, Fonts, Spacing

class SidebarFrame(ctk.CTkFrame):
    """
    Left sidebar with navigation buttons.
    Modern Dark Navy style with icon-text layout.
    """
    # Nav items configuration: (icon, label, view_name)
    NAV_ITEMS = [
        ("🏠", "Dashboard",  "dashboard"),
        ("📚", "Thư viện",   "library"),
        ("⚙️", "Cài đặt",   "settings"),
    ]

    def __init__(self, master, on_navigate: Callable, on_close_book: Optional[Callable] = None, **kwargs):
        super().__init__(
            master, 
            width=Spacing.SIDEBAR_WIDTH, 
            corner_radius=0, 
            fg_color=Colors.BG_SIDEBAR,
            border_width=0,
            **kwargs
        )
        self.on_navigate = on_navigate
        self.on_close_book = on_close_book
        self.buttons = {}  # view_name -> button widget
        
        # Prevent sidebar from shrinking
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        
        # === Logo / Brand ===
        logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        logo_frame.pack(fill="x", padx=Spacing.LG, pady=(Spacing.XL, Spacing.SM))
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(
            logo_frame, text="E-Extract", 
            font=Fonts.LOGO,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        ).pack(side="left", fill="x")
        
        # === Section Label: MENU ===
        ctk.CTkLabel(
            self, text="MENU", font=Fonts.NAV_LABEL,
            text_color=Colors.TEXT_MUTED, anchor="w"
        ).pack(fill="x", padx=Spacing.XL, pady=(Spacing.LG, Spacing.XS))
        
        # === Navigation Buttons ===
        for icon, label, view_name in self.NAV_ITEMS:
            btn = self._create_nav_button(icon, label, view_name)
            self.buttons[view_name] = btn
        
        # === Separator ===
        sep = ctk.CTkFrame(self, height=1, fg_color=Colors.BORDER)
        sep.pack(fill="x", padx=Spacing.LG, pady=(Spacing.LG, Spacing.SM))
        
        # === Active Book Section (Hidden by default) ===
        self.book_section = ctk.CTkFrame(self, fg_color="transparent")
        # Don't pack yet - will be shown/hidden

        ctk.CTkLabel(
            self.book_section, text="ĐANG MỞ", font=Fonts.NAV_LABEL,
            text_color=Colors.TEXT_MUTED, anchor="w"
        ).pack(fill="x", padx=Spacing.XL, pady=(Spacing.SM, Spacing.XS))
        
        self.btn_active_book = self._create_nav_button("📄", "Xem nội dung", "results", parent=self.book_section)
        self.buttons["results"] = self.btn_active_book
        
        self.btn_close_book = ctk.CTkButton(
            self.book_section,
            text="   ✕  Đóng sách",
            fg_color="transparent",
            text_color=Colors.DANGER,
            hover_color=Colors.BG_CARD_HOVER,
            anchor="w",
            height=Spacing.NAV_BUTTON_H,
            corner_radius=Spacing.BUTTON_RADIUS,
            font=Fonts.NAV,
            command=self._handle_close_book
        )
        self.btn_close_book.pack(fill="x", padx=Spacing.MD, pady=(0, Spacing.XS))

        # === Spacer (pushes version to bottom) ===
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)
        
        # === Bottom: Version ===
        ctk.CTkLabel(
            self, text="v2.0.0 — Dark Navy", font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED
        ).pack(pady=(Spacing.SM, Spacing.LG))
        
        # Initial State
        self.hide_active_book_controls()

    def _create_nav_button(self, icon: str, label: str, view_name: str, parent=None) -> ctk.CTkButton:
        """Create a styled navigation button."""
        container = parent or self
        text = f"   {icon}  {label}"
        btn = ctk.CTkButton(
            container,
            text=text,
            fg_color="transparent",
            text_color=Colors.TEXT_SECONDARY,
            hover_color=Colors.SIDEBAR_HOVER,
            anchor="w",
            height=Spacing.NAV_BUTTON_H,
            corner_radius=Spacing.BUTTON_RADIUS,
            font=Fonts.NAV,
            command=lambda: self.on_navigate(view_name)
        )
        btn.pack(fill="x", padx=Spacing.MD, pady=2)
        return btn
    
    def _handle_close_book(self) -> None:
        if self.on_close_book:
            self.on_close_book()

    def set_active_button(self, view_name: str) -> None:
        """Highlight the active navigation button."""
        for name, btn in self.buttons.items():
            if name == view_name:
                btn.configure(
                    fg_color=Colors.SIDEBAR_ACTIVE,
                    text_color=Colors.PRIMARY,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Colors.TEXT_SECONDARY,
                )

    def show_active_book_controls(self, book_title: str = "Book") -> None:
        """Show the controls for the active book."""
        self.book_section.pack(fill="x", after=list(self.children.values())[4]) # After separator

    def hide_active_book_controls(self) -> None:
        """Hide the controls for the active book."""
        self.book_section.pack_forget()
