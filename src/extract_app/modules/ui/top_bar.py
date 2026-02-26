# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/top_bar.py
# Version: 2.0.0
# Author: Antigravity
# Description: Top bar component displaying file context (Dark Navy style).
# --------------------------------------------------------------------------------

"""
Top bar component — Dark Navy style.
"""
from typing import Callable
import customtkinter as ctk
from .theme import Colors, Fonts, Spacing

class TopBarFrame(ctk.CTkFrame):
    """
    Top bar displaying current context/file path and close action.
    Minimal, blends with the Dark Navy theme.
    """
    def __init__(self, master, on_close: Callable = None, **kwargs):
        super().__init__(
            master, height=44, corner_radius=0, 
            fg_color=Colors.BG_APP, 
            border_width=0,
            **kwargs
        )
        self.on_close = on_close
        self.pack_propagate(False)
        
        # Inner layout
        self.grid_columnconfigure(0, weight=1)

        self.path_label = ctk.CTkLabel(
            self, text="", font=Fonts.SMALL, 
            text_color=Colors.TEXT_MUTED, anchor="w"
        )
        self.path_label.grid(row=0, column=0, padx=Spacing.XL, pady=Spacing.SM, sticky="ew")

        # Close Button (hidden initially)
        self.close_btn = ctk.CTkButton(
            self, 
            text="✕ Đóng", 
            width=70, 
            height=28, 
            fg_color="transparent", 
            text_color=Colors.TEXT_MUTED,
            hover_color=Colors.BG_CARD_HOVER,
            corner_radius=Spacing.BUTTON_RADIUS,
            font=Fonts.SMALL,
            command=self._on_close_click
        )

    def set_file_path(self, path: str):
        """Update the displayed file path and toggle close button."""
        if not path:
            self.path_label.configure(text="")
            self.close_btn.grid_forget()
            return
            
        display_text = f"📂  {path}"
        self.path_label.configure(text=display_text)
        self.close_btn.grid(row=0, column=1, padx=Spacing.MD)

    def _on_close_click(self):
        if self.on_close:
            self.on_close()
