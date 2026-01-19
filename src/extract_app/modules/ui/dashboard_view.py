"""
Dashboard/Welcome view.
"""
from typing import Callable
import customtkinter as ctk

class DashboardView(ctk.CTkFrame):
    """
    Home screen with large import button.
    """
    def __init__(self, master, on_import: Callable, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_import = on_import
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=1, column=0, sticky="ns")
        
        self.welcome_label = ctk.CTkLabel(
            self.center_frame, 
            text="Chào mừng trở lại!", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.welcome_label.pack(pady=(0, 10))

        self.sub_label = ctk.CTkLabel(
            self.center_frame,
            text="Bắt đầu trích xuất nội dung từ Ebook của bạn.",
            font=ctk.CTkFont(size=16)
        )
        self.sub_label.pack(pady=(0, 40))

        self.import_btn = ctk.CTkButton(
            self.center_frame,
            text="CHỌN TỆP EBOOK (PDF/EPUB)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            width=250,
            corner_radius=25,
            command=self.on_import
        )
        self.import_btn.pack(pady=10)
        
        self.info_label = ctk.CTkLabel(
            self.center_frame,
            text="Hỗ trợ: .epub, .pdf (văn bản)",
            text_color="gray"
        )
        self.info_label.pack(pady=5)
