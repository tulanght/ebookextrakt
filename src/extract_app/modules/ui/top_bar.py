"""
Top bar component.
"""
from typing import Callable
import customtkinter as ctk

class TopBarFrame(ctk.CTkFrame):
    """
    Top bar displaying current context/file path and close action.
    """
    def __init__(self, master, on_close: Callable = None, **kwargs):
        super().__init__(master, height=40, corner_radius=0, fg_color="transparent", **kwargs)
        self.on_close = on_close
        self.grid_columnconfigure(0, weight=1)

        self.path_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color="gray", anchor="w"
        )
        self.path_label.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        # Close Button (Initially hidden or disabled)
        self.close_btn = ctk.CTkButton(
            self, 
            text="✕ Đóng", 
            width=60, 
            height=24, 
            fg_color="transparent", 
            text_color="gray",
            hover_color=("gray90", "gray20"),
            command=self._on_close_click
        )
        # We don't grid it yet, or grid it and hide it

    def set_file_path(self, path: str):
        """Update the displayed file path and toggle close button."""
        if not path:
            self.path_label.configure(text="")
            self.close_btn.grid_forget()
            return
            
        display_text = f"Đang xử lý: {path}"
        self.path_label.configure(text=display_text)
        self.close_btn.grid(row=0, column=1, padx=10)

    def _on_close_click(self):
        if self.on_close:
            self.on_close()
