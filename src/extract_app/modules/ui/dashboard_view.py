"""
Dashboard/Welcome view.
"""
from typing import Callable, List, Dict
from functools import partial
from pathlib import Path
import customtkinter as ctk

class DashboardView(ctk.CTkFrame):
    """
    Home screen with large import button.
    """
    def __init__(self, master, on_import: Callable, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_import = on_import
        
        # 2. Main Action Area
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Welcome Text
        self.welcome_label = ctk.CTkLabel(
            self.action_frame, 
            text="Chào mừng đến với ExtractPDF-EPUB",
            font=("", 24, "bold")
        )
        self.welcome_label.pack(pady=(40, 10))

        self.sub_label = ctk.CTkLabel(
            self.action_frame,
            text="Công cụ trích xuất nội dung Ebook mạnh mẽ & nhanh chóng",
            font=("", 14),
            text_color="gray"
        )
        self.sub_label.pack(pady=(0, 30))

        # Import Button
        self.import_btn = ctk.CTkButton(
            self.action_frame,
            text="MỞ FILE (PDF/EPUB)",
            width=200,
            height=50,
            font=("", 15, "bold"),
            command=self.on_import
        )
        self.import_btn.pack(pady=10)
        
        # Recent Files Section
        self.history_frame = ctk.CTkScrollableFrame(self.action_frame, label_text="Gần đây", width=400, height=200)
        self.history_frame.pack(pady=(40, 0), fill="both", expand=True)
        # Placeholder
        self.no_history_label = ctk.CTkLabel(self.history_frame, text="Chưa có lịch sử.", text_color="gray")
        self.no_history_label.pack(pady=10)

        self.info_label = ctk.CTkLabel(
            self.action_frame, # Changed parent to action_frame
            text="Hỗ trợ: .epub, .pdf (văn bản)",
            text_color="gray"
        )
        self.info_label.pack(pady=5) # Kept original packing

    def update_history(self, history_list: List[Dict], open_callback: Callable[[str], None]):
        """Update the Recent Files list."""
        # Clear existing
        for widget in self.history_frame.winfo_children():
            widget.destroy()
            
        if not history_list:
            lbl = ctk.CTkLabel(self.history_frame, text="Chưa có lịch sử.", text_color="gray")
            lbl.pack(pady=10)
            return

        for item in history_list:
            filepath = item.get('filepath')
            title = item.get('title', Path(filepath).name)
            
            # Row container
            row = ctk.CTkFrame(self.history_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            # Button (as label-like or clickable)
            # Using Button for interaction
            btn = ctk.CTkButton(
                row, 
                text=f"{title}", 
                anchor="w", 
                fg_color="transparent", 
                border_width=1,
                border_color=("gray70", "gray30"),
                text_color=("black", "white"),
                command=partial(open_callback, filepath)
            )
            btn.pack(side="left", fill="x", expand=True, padx=5)
            
            # Tooltip/Path label? Too complex for now. user can see title.

