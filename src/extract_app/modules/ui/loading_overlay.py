# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/loading_overlay.py
# Version: 1.0.0
# Author: Antigravity
# Description: An overlay component to show loading status and progress.
# --------------------------------------------------------------------------------

import customtkinter as ctk

class LoadingOverlay(ctk.CTkFrame):
    """
    An overlay frame that covers the content area to show progress.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=("gray95", "gray10"), **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Center container
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=0, column=0)
        
        self.status_label = ctk.CTkLabel(
            self.center_frame, text="Processing...", font=("", 16, "bold")
        )
        self.status_label.pack(pady=(0, 20))
        
        self.progress_bar = ctk.CTkProgressBar(self.center_frame, width=400, mode="indeterminate")
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()
        
        self.detail_label = ctk.CTkLabel(
            self.center_frame, text="Please wait...", text_color="gray"
        )
        self.detail_label.pack(pady=(10, 0))

    def update_status(self, title: str = None, detail: str = None, progress: float = None):
        """
        Update the loading status.
        
        Args:
            title (str): Main status text (e.g. "Extracting...")
            detail (str): Subtitle text (e.g. "Chapter 5/10")
            progress (float): 0.0 to 1.0. If provided, switches to 'determinate' mode. 
                              If None, keeps 'indeterminate'.
        """
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
