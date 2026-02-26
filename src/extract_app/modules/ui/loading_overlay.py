# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/loading_overlay.py
# Version: 2.0.0
# Description: Loading overlay with Dark Navy theme.
# --------------------------------------------------------------------------------

import customtkinter as ctk
from .theme import Colors, Fonts, Spacing

class LoadingOverlay(ctk.CTkFrame):
    """An overlay frame that covers the content area to show progress."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=Colors.BG_APP, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Center container (card)
        self.center_frame = ctk.CTkFrame(
            self, fg_color=Colors.BG_CARD,
            corner_radius=Spacing.CARD_RADIUS,
            border_width=1, border_color=Colors.BORDER
        )
        self.center_frame.grid(row=0, column=0)
        self.center_frame.configure(width=420, height=180)
        self.center_frame.grid_propagate(False)
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_rowconfigure((0, 1, 2), weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.center_frame, text="Đang xử lý...", 
            font=Fonts.H3, text_color=Colors.TEXT_PRIMARY
        )
        self.status_label.grid(row=0, column=0, pady=(Spacing.XL, Spacing.SM))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.center_frame, width=360, mode="indeterminate",
            progress_color=Colors.PRIMARY,
            fg_color=Colors.BORDER,
            height=6,
            corner_radius=3
        )
        self.progress_bar.grid(row=1, column=0, pady=Spacing.SM)
        self.progress_bar.start()
        
        self.detail_label = ctk.CTkLabel(
            self.center_frame, text="Vui lòng chờ...", 
            text_color=Colors.TEXT_MUTED, font=Fonts.SMALL
        )
        self.detail_label.grid(row=2, column=0, pady=(0, Spacing.XL))

    def update_status(self, title=None, detail=None, progress=None):
        if title:
            self.status_label.configure(text=title)
        if detail:
            self.detail_label.configure(text=detail)
        if progress is not None:
            if self.progress_bar.cget("mode") != "determinate":
                self.progress_bar.configure(mode="determinate")
                self.progress_bar.stop()
            self.progress_bar.set(progress)
        else:
            if self.progress_bar.cget("mode") != "indeterminate":
                self.progress_bar.configure(mode="indeterminate")
                self.progress_bar.start()
