# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/glossary_tab.py
# Version: 1.0.0
# Description: Glossary Management UI for Settings.
# --------------------------------------------------------------------------------

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from .theme import Colors, Fonts, Spacing

class GlossaryTab(ctk.CTkFrame):
    """
    UI Component for managing dictionary terms categorized by subject.
    Embedded inside SettingsView and SettingsWindow.
    """
    
    def __init__(self, parent, glossary_manager):
        super().__init__(parent, fg_color="transparent")
        self.glossary_manager = glossary_manager
        
        self.cats = self.glossary_manager.get_categories()
        self.active_cat_var = tk.StringVar(value=self.glossary_manager.get_active_category())
        
        self._build_ui()
        self._refresh_terms()

    def _build_ui(self):
        # 1. Category Top Bar
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", pady=Spacing.SM)
        
        ctk.CTkLabel(top_frame, text="Danh mục:", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        self.cat_menu = ctk.CTkOptionMenu(
            top_frame, variable=self.active_cat_var, values=self.cats, width=150,
            command=self._on_category_change,
            fg_color=Colors.BG_INPUT, button_color=Colors.BORDER, button_hover_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY, dropdown_fg_color=Colors.BG_CARD, dropdown_text_color=Colors.TEXT_PRIMARY
        )
        self.cat_menu.pack(side="left", padx=Spacing.SM)
        
        ctk.CTkButton(
            top_frame, text="Thêm", width=60, command=self._add_category,
            fg_color=Colors.BG_CARD, hover_color=Colors.BG_CARD_HOVER, border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="left", padx=(0, Spacing.SM))
        
        ctk.CTkButton(
            top_frame, text="Xóa", width=60, command=self._delete_category,
            fg_color=Colors.DANGER, hover_color=Colors.DANGER_HOVER, border_width=0,
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="left")

        # 2. Terms List (Scrollable)
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=Colors.BG_APP, corner_radius=Spacing.CARD_RADIUS,
            scrollbar_button_color=Colors.BORDER, scrollbar_button_hover_color=Colors.TEXT_MUTED
        )
        self.list_frame.pack(fill="both", expand=True, pady=Spacing.SM)

        # 3. Add Term Bottom Bar
        bottom_frame = ctk.CTkFrame(self, fg_color=Colors.BG_APP, corner_radius=Spacing.CARD_RADIUS)
        bottom_frame.pack(fill="x", pady=(0, Spacing.SM), ipady=Spacing.SM, padx=0)
        
        ctk.CTkLabel(bottom_frame, text="Thêm từ mới:", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).grid(row=0, column=0, columnspan=3, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))
        
        self.en_entry = ctk.CTkEntry(bottom_frame, placeholder_text="Tiếng Anh (VD: habitat)", width=200, fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY)
        self.en_entry.grid(row=1, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM, sticky="we")
        
        self.vi_entry = ctk.CTkEntry(bottom_frame, placeholder_text="Tiếng Việt (VD: môi trường sống)", width=200, fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, text_color=Colors.TEXT_PRIMARY)
        self.vi_entry.grid(row=1, column=1, padx=(0, Spacing.SM), pady=Spacing.SM, sticky="we")
        
        ctk.CTkButton(
            bottom_frame, text="Thêm", width=80, command=self._add_term,
            fg_color=Colors.SUCCESS, hover_color=Colors.SUCCESS_HOVER, text_color=Colors.TEXT_PRIMARY
        ).grid(row=1, column=2, padx=(0, Spacing.MD), pady=Spacing.SM)
        
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)

    def _refresh_terms(self):
        """Redraw the terms list for the active category."""
        # Clear existing
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        active_cat = self.active_cat_var.get()
        terms = self.glossary_manager.get_terms(active_cat)
        
        if not terms:
            ctk.CTkLabel(self.list_frame, text="Chưa có từ vựng nào trong danh mục này.", text_color=Colors.TEXT_MUTED, font=Fonts.BODY).pack(pady=Spacing.LG)
            return

        for i, (en, vi) in enumerate(terms.items()):
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=en, width=150, anchor="w", font=Fonts.BODY_BOLD, text_color=Colors.PRIMARY).pack(side="left", padx=Spacing.SM)
            ctk.CTkLabel(row, text="→", width=30, text_color=Colors.TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=vi, anchor="w", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=Spacing.SM, fill="x", expand=True)
            
            ctk.CTkButton(
                row, text="Xóa", width=50, height=24,
                fg_color="transparent", hover_color=Colors.DANGER, text_color=Colors.DANGER,
                border_width=1, border_color=Colors.DANGER,
                command=lambda e=en: self._delete_term(e)
            ).pack(side="right", padx=Spacing.SM)

    def _on_category_change(self, choice):
        self.glossary_manager.set_active_category(choice)
        self._refresh_terms()

    def _add_category(self):
        dialog = ctk.CTkInputDialog(text="Tên danh mục mới (VD: Biology, History):", title="Thêm Danh mục")
        new_cat = dialog.get_input()
        if new_cat and new_cat.strip():
            new_cat = new_cat.strip()
            self.glossary_manager.add_category(new_cat)
            self.cats = self.glossary_manager.get_categories()
            self.cat_menu.configure(values=self.cats)
            self.active_cat_var.set(new_cat)
            self._on_category_change(new_cat)

    def _delete_category(self):
        cat = self.active_cat_var.get()
        if cat == "General":
            messagebox.showwarning("Lỗi", "Không thể xóa danh mục General mặc định.")
            return
            
        if tk.messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa danh mục '{cat}' và toàn bộ từ vựng bên trong?"):
            self.glossary_manager.set_active_category("General") # Switch away before delete
            if self.glossary_manager.delete_category(cat):
                self.cats = self.glossary_manager.get_categories()
                self.cat_menu.configure(values=self.cats)
                self.active_cat_var.set("General")
                self._on_category_change("General")

    def _add_term(self):
        en = self.en_entry.get().strip()
        vi = self.vi_entry.get().strip()
        if en and vi:
            self.glossary_manager.add_term(en, vi, self.active_cat_var.get())
            self.en_entry.delete(0, 'end')
            self.vi_entry.delete(0, 'end')
            self._refresh_terms()

    def _delete_term(self, en_term):
        self.glossary_manager.delete_term(en_term, self.active_cat_var.get())
        self._refresh_terms()
