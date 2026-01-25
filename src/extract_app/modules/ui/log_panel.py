# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/log_panel.py
# Version: 1.0.0
# Author: Antigravity
# Description: A UI component for displaying application logs in real-time.
# --------------------------------------------------------------------------------

import tkinter as tk
from datetime import datetime
import customtkinter as ctk

class LogPanel(ctk.CTkFrame):
    """
    A collapsible panel for displaying logs.
    """
    def __init__(self, master, height=150, **kwargs):
        super().__init__(master, height=height, **kwargs)
        self.pack_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Header (Title + Buttons)
        self.header_frame = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, text="Application Logs", font=("", 12, "bold")
        )
        self.title_label.pack(side="left", padx=5)

        self.btn_clear = ctk.CTkButton(
            self.header_frame, text="Clear", width=60, height=20, 
            command=self.clear_logs, font=("", 10)
        )
        self.btn_clear.pack(side="right", padx=5)

        # 2. Log Display (ScrolledText)
        # Note: CTkTextbox is effectively a ScrolledText
        self.log_text = ctk.CTkTextbox(
            self, font=("Consolas", 10), state="disabled", wrap="word"
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Tags for coloring (simulated/simple for now)
        # CTkTextbox doesn't support full tag configuration like tk.Text easily without accessing internal widget
        # For simplicity, we stick to monochrome or basic text usage for v1.0

    def write_log(self, message: str):
        """
        Append a message to the log panel.
        Thread-safe wrapper usually needed, but tkinter requires main thread usage.
        Consumers should ensure this is called from main thread or use after().
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.configure(state="normal")
        self.log_text.insert("end", formatted_message)
        self.log_text.see("end") # Auto-scroll
        self.log_text.configure(state="disabled")

    def clear_logs(self):
        """Clear all logs."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
