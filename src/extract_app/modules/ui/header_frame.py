"""
Header frame component for the ExtractPDF-EPUB application.
Handles file selection and save location controls.
"""
from pathlib import Path
from typing import Callable, List
import customtkinter as ctk

class HeaderFrame(ctk.CTkFrame):
    """
    Top header frame with file selection and save controls.
    """
    def __init__(
        self,
        master,
        on_select_callback: Callable,
        on_save_callback: Callable,
        recent_save_paths: List[str],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_select_callback = on_select_callback
        self.on_save_callback = on_save_callback
        self.recent_save_paths = recent_save_paths
        
        # UI Attributes
        self.select_button: ctk.CTkButton
        self.save_path_combobox: ctk.CTkComboBox
        self.save_button: ctk.CTkButton
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create and layout the widgets."""
        self.grid_columnconfigure(1, weight=1)

        self.select_button = ctk.CTkButton(
            self, text="Chọn Ebook...", command=self.on_select_callback
        )
        self.select_button.grid(row=0, column=0, padx=10, pady=10)

        save_path_frame = ctk.CTkFrame(self, fg_color="transparent")
        save_path_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        save_path_frame.grid_columnconfigure(1, weight=1)

        save_label = ctk.CTkLabel(save_path_frame, text="Lưu vào:")
        save_label.grid(row=0, column=0, padx=(0, 5))

        self.save_path_combobox = ctk.CTkComboBox(save_path_frame, values=self.recent_save_paths)
        self.save_path_combobox.grid(row=0, column=1, sticky="ew")
        
        # Initialize default path if empty
        if not self.recent_save_paths:
             self._setup_default_save_path()
        elif self.recent_save_paths:
             self.save_path_combobox.set(self.recent_save_paths[-1])

        self.save_button = ctk.CTkButton(
            self, text="Lưu kết quả", command=self.on_save_callback, state="disabled"
        )
        self.save_button.grid(row=0, column=2, padx=10, pady=10)

    def _setup_default_save_path(self):
        """Create and set the default 'Output' directory if needed."""
        default_path = Path.cwd() / "Output"
        default_path.mkdir(exist_ok=True)
        path_str = str(default_path)
        if path_str not in self.recent_save_paths:
            self.recent_save_paths.append(path_str)
        
        self.save_path_combobox.configure(values=self.recent_save_paths)
        self.save_path_combobox.set(path_str)

    def get_save_path(self) -> str:
        """Return the current selected save path."""
        return self.save_path_combobox.get()
    
    def set_buttons_state(self, state: str):
        """Enable or disable header buttons (normal/disabled)."""
        self.select_button.configure(state=state)
        # We generally only enable save if there are results, handling that separately or 
        # allowing this generic setter. For fine-grained control:
        if state == "disabled":
            self.save_button.configure(state="disabled")
            
    def set_save_button_state(self, state: str):
        """Specifically set save button state."""
        self.save_button.configure(state=state)
    
    def set_select_button_state(self, state: str):
        """Specifically set select button state."""
        self.select_button.configure(state=state)
