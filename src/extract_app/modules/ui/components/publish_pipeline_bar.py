# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/components/publish_pipeline_bar.py
# Version: 1.0.0
# Author: Antigravity
# Description: A UI Component to display a 5-step progress bar for publishing.
# --------------------------------------------------------------------------------

import customtkinter as ctk
from src.extract_app.modules.ui.theme import Colors, Fonts, Spacing

class PublishPipelineBar(ctk.CTkFrame):
    """
    Displays the 5-step publishing pipeline progress:
    Research -> Outline -> Dịch thuật -> Thumbnail -> Tối ưu SEO
    """
    STEPS = ["Research", "Outline", "Dịch thuật", "Thumbnail", "Tối ưu SEO"]
    
    def __init__(self, master, current_step: int = 2, **kwargs):
        super().__init__(master, fg_color="transparent", height=40, **kwargs)
        self.current_step = current_step
        self.step_labels = []
        self._build_ui()
        
    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill="both")
        
        for i, step_name in enumerate(self.STEPS):
            # Step Container
            step_frame = ctk.CTkFrame(container, fg_color="transparent")
            step_frame.pack(side="left", padx=Spacing.SM)
            
            # Icon / Indicator
            is_done = i < self.current_step
            is_active = i == self.current_step
            
            if is_done:
                color = Colors.SUCCESS
                icon = "✓"
                font = Fonts.BODY_BOLD
            elif is_active:
                color = Colors.PRIMARY
                icon = "●"
                font = Fonts.BODY_BOLD
            else:
                color = Colors.BORDER_ACCENT
                icon = "○"
                font = Fonts.BODY
                
            lbl_icon = ctk.CTkLabel(
                step_frame, text=icon, width=20, 
                text_color=color, font=Fonts.BODY_BOLD
            )
            lbl_icon.pack(side="left")
            
            lbl_text = ctk.CTkLabel(
                step_frame, text=step_name, 
                text_color=color if (is_done or is_active) else Colors.TEXT_MUTED,
                font=font
            )
            lbl_text.pack(side="left", padx=(4, 0))
            self.step_labels.append((lbl_icon, lbl_text))
            
            # Separator line if not the last step
            if i < len(self.STEPS) - 1:
                sep_color = Colors.SUCCESS if is_done else Colors.BORDER_ACCENT
                sep = ctk.CTkFrame(container, width=30, height=2, fg_color=sep_color)
                sep.pack(side="left", padx=Spacing.SM)
                
    def set_step(self, step_idx: int):
        self.current_step = step_idx
        for widget in self.winfo_children():
            widget.destroy()
        self.step_labels = []
        self._build_ui()
