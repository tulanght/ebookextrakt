# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/log_panel.py
# Version: 2.0.0
# Description: Themed log panel with Dark Navy style.
# --------------------------------------------------------------------------------

import tkinter as tk
from datetime import datetime
import customtkinter as ctk
from .theme import Colors, Fonts, Spacing

class LogPanel(ctk.CTkFrame):
    """A panel for displaying application logs."""
    def __init__(self, master, height=120, **kwargs):
        super().__init__(
            master, height=height, 
            fg_color=Colors.BG_CARD, 
            corner_radius=Spacing.CARD_RADIUS,
            border_width=1, border_color=Colors.BORDER,
            **kwargs
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        
        ctk.CTkLabel(
            self.header_frame, text="📋  Logs", 
            font=Fonts.BODY_BOLD, text_color=Colors.TEXT_MUTED
        ).pack(side="left")

        ctk.CTkButton(
            self.header_frame, text="Clear", width=50, height=20, 
            fg_color="transparent", hover_color=Colors.BG_CARD_HOVER,
            text_color=Colors.TEXT_MUTED,
            command=self.clear_logs, font=Fonts.TINY,
            corner_radius=4
        ).pack(side="right")

        # Log Text
        self.log_text = ctk.CTkTextbox(
            self, font=("Consolas", 10), state="disabled", wrap="word",
            fg_color=Colors.BG_INPUT, text_color=Colors.TEXT_MUTED,
            border_width=0, corner_radius=Spacing.BUTTON_RADIUS,
            scrollbar_button_color=Colors.BORDER,
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.SM)

    def write_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", formatted_message)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_logs(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
