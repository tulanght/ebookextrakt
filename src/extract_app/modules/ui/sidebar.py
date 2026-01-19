"""
Sidebar navigation component.
"""
from typing import Callable
import customtkinter as ctk

class SidebarFrame(ctk.CTkFrame):
    """
    Left sidebar with navigation buttons.
    """
    def __init__(self, master, on_navigate: Callable, **kwargs):
        super().__init__(master, width=200, corner_radius=0, **kwargs)
        self.on_navigate = on_navigate
        self.grid_rowconfigure(4, weight=1)

        # Logo / Title
        self.logo_label = ctk.CTkLabel(
            self, text="E-Extract", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Navigation Buttons
        self.btn_dashboard = self._create_nav_button("Dashboard", 1, "dashboard")
        self.btn_library = self._create_nav_button("Thư viện", 2, "library")
        self.btn_settings = self._create_nav_button("Cài đặt", 3, "settings")
        # Library and Settings are placeholders for now, but good to have in UI

        # Bottom info
        self.version_label = ctk.CTkLabel(
            self, text="v1.0.0", text_color="gray", font=ctk.CTkFont(size=10)
        )
        self.version_label.grid(row=5, column=0, padx=20, pady=20)

    def _create_nav_button(self, text, row, view_name):
        btn = ctk.CTkButton(
            self,
            text=text,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=lambda: self.on_navigate(view_name)
        )
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        return btn

    def set_active_button(self, view_name: str):
        """Highlight the active navigation button."""
        buttons = {
            "dashboard": self.btn_dashboard,
            "library": self.btn_library,
            "settings": self.btn_settings
        }
        
        for name, btn in buttons.items():
            if name == view_name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")
