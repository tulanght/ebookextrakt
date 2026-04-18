# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/wp_sites_tab.py
# Version: 1.0.0
# Description: Configuration UI for managing WordPress publishing sites.
# --------------------------------------------------------------------------------

import customtkinter as ctk
import tkinter as tk
from typing import Dict, List
import json
from .theme import Colors, Fonts, Spacing
from .custom_dialog import show_info, show_error, ask_yes_no
from ...core.wordpress_api_client import WordPressAPIClient

class WPSitesTab(ctk.CTkFrame):
    def __init__(self, parent, settings_manager):
        super().__init__(parent, fg_color="transparent")
        self.settings_manager = settings_manager
        
        # Load sites from settings
        sites_data = self.settings_manager.get_wp_sites()
        # Create deep copy so we can edit without saving immediately
        self.sites: List[Dict] = json.loads(json.dumps(sites_data))
        self.current_site_index = -1
        self.current_templates = {}
        
        self._build_ui()
        self._refresh_site_list()

    def _build_ui(self):
        # Top bar: Site selection and Add/Remove
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", pady=Spacing.SM)
        
        ctk.CTkLabel(top_bar, text="Chọn Website:", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        self.site_selector_var = tk.StringVar(value="")
        # Use Label + Prev/Next buttons to avoid CTkComboBox menu allocation
        self.btn_prev_site = ctk.CTkButton(
            top_bar, text="◀", width=30, height=32,
            fg_color=Colors.BG_CARD, hover_color=Colors.BG_CARD_HOVER,
            border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            command=self._prev_site
        )
        self.btn_prev_site.pack(side="left", padx=(Spacing.SM, 2))
        
        self.site_selector = ctk.CTkLabel(
            top_bar, textvariable=self.site_selector_var,
            width=180, anchor="center",
            fg_color=Colors.BG_INPUT, corner_radius=6,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.BODY
        )
        self.site_selector.pack(side="left", padx=2)
        
        self.btn_next_site = ctk.CTkButton(
            top_bar, text="▶", width=30, height=32,
            fg_color=Colors.BG_CARD, hover_color=Colors.BG_CARD_HOVER,
            border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            command=self._next_site
        )
        self.btn_next_site.pack(side="left", padx=(2, Spacing.SM))
        
        ctk.CTkButton(top_bar, text="Thêm Site", width=80, command=self._add_site).pack(side="left", padx=(Spacing.MD, 0))
        ctk.CTkButton(top_bar, text="Xóa Site", width=80, fg_color=Colors.DANGER, hover_color=Colors.DANGER_HOVER, command=self._delete_site).pack(side="left", padx=Spacing.SM)

        # Main scrollable container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, pady=Spacing.SM)
        
        # Site Info Form
        info_frame = ctk.CTkFrame(self.scroll, fg_color=Colors.BG_CARD)
        info_frame.pack(fill="x", pady=Spacing.SM, ipady=Spacing.SM, padx=Spacing.SM)
        
        self._add_form_row(info_frame, "ID (Internal):", "site_id_var")
        self._add_form_row(info_frame, "Display Name:", "site_name_var")
        self._add_form_row(info_frame, "URL (không có / ở cuối):", "site_url_var")
        self._add_form_row(info_frame, "Username:", "site_user_var")
        self._add_form_row(info_frame, "App Password:", "site_pass_var", is_password=True)
        
        test_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        test_frame.pack(fill="x", pady=Spacing.SM, padx=Spacing.MD)
        ctk.CTkButton(test_frame, text="Test Connection", fg_color=Colors.PRIMARY, command=self._test_connection).pack(side="left")
        self.test_status_label = ctk.CTkLabel(test_frame, text="", text_color=Colors.SUCCESS)
        self.test_status_label.pack(side="left", padx=Spacing.MD)

        # Categories
        cat_frame = ctk.CTkFrame(self.scroll, fg_color=Colors.BG_CARD)
        cat_frame.pack(fill="x", pady=Spacing.SM, ipady=Spacing.SM, padx=Spacing.SM)
        ctk.CTkLabel(cat_frame, text="Category Map (JSON Format):", font=Fonts.BODY_BOLD).pack(anchor="w", padx=Spacing.MD, pady=Spacing.SM)
        
        self.cat_textbox = ctk.CTkTextbox(cat_frame, height=100, font=Fonts.CODE)
        self.cat_textbox.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
        ctk.CTkLabel(cat_frame, text='Ví dụ: [{"slug": "thu", "wp_id": 5, "keywords": ["hổ", "sư tử"]}]', text_color=Colors.TEXT_MUTED).pack(anchor="w", padx=Spacing.MD)

        # Templates
        tpl_frame = ctk.CTkFrame(self.scroll, fg_color=Colors.BG_CARD)
        tpl_frame.pack(fill="x", pady=Spacing.SM, ipady=Spacing.SM, padx=Spacing.SM)
        ctk.CTkLabel(tpl_frame, text="Article Templates:", font=Fonts.BODY_BOLD).pack(anchor="w", padx=Spacing.MD, pady=Spacing.SM)
        
        tpl_tools = ctk.CTkFrame(tpl_frame, fg_color="transparent")
        tpl_tools.pack(fill="x", padx=Spacing.MD)
        self.tpl_type_var = tk.StringVar(value="general")
        self.tpl_menu = ctk.CTkSegmentedButton(
            tpl_tools, variable=self.tpl_type_var, 
            values=["general", "species_profile", "comparison"],
            command=self._on_template_type_changed
        )
        self.tpl_menu.pack(side="left")
        
        self.tpl_textbox = ctk.CTkTextbox(tpl_frame, height=150)
        self.tpl_textbox.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)

        # Save Button
        ctk.CTkButton(self, text="Lưu Cài Đặt WP", height=40, font=Fonts.BODY_BOLD, fg_color=Colors.SUCCESS, hover_color=Colors.SUCCESS_HOVER, command=self._save_changes).pack(pady=Spacing.MD)

    def _add_form_row(self, parent, label_text, var_name, is_password=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=Spacing.MD, pady=4)
        ctk.CTkLabel(row, text=label_text, width=160, anchor="w", font=Fonts.BODY).pack(side="left")
        var = tk.StringVar()
        setattr(self, var_name, var)
        entry = ctk.CTkEntry(row, textvariable=var, show="*" if is_password else "", height=32, placeholder_text=label_text)
        entry.pack(side="left", fill="x", expand=True)

    def _prev_site(self) -> None:
        """Navigate to the previous site."""
        if self.current_site_index > 0:
            if self.current_site_index >= 0:
                self._flush_current_site_changes(silent=True)
            self.current_site_index -= 1
            self._load_site_data(self.current_site_index)
            self._update_site_selector_label()

    def _next_site(self) -> None:
        """Navigate to the next site."""
        if self.current_site_index < len(self.sites) - 1:
            if self.current_site_index >= 0:
                self._flush_current_site_changes(silent=True)
            self.current_site_index += 1
            self._load_site_data(self.current_site_index)
            self._update_site_selector_label()

    def _update_site_selector_label(self) -> None:
        """Refresh the site label display."""
        if not self.sites or self.current_site_index < 0:
            self.site_selector_var.set("No sites")
        else:
            total = len(self.sites)
            name = self.sites[self.current_site_index].get("display_name", "Unnamed")
            self.site_selector_var.set(f"{self.current_site_index + 1}/{total}: {name}")

    def _refresh_site_list(self):
        if not self.sites:
            self.current_site_index = -1
            self._clear_ui()
        else:
            if self.current_site_index < 0:
                self.current_site_index = 0
            elif self.current_site_index >= len(self.sites):
                self.current_site_index = len(self.sites) - 1
            self._load_site_data(self.current_site_index)

        self._update_site_selector_label()
            
    def _clear_ui(self):
        """Clears the form when no site is selected."""
        for var in [self.site_id_var, self.site_name_var, self.site_url_var, self.site_user_var, self.site_pass_var]:
            var.set("")
        self.cat_textbox.delete("1.0", "end")
        self.tpl_textbox.delete("1.0", "end")
            
    def _on_site_selected(self, value):
        # Save current state before switching
        if self.current_site_index >= 0:
            self._flush_current_site_changes(silent=True)
            
        names = [site.get("display_name", site.get("id", "Unnamed")) for site in self.sites]
        if value in names:
            self.current_site_index = names.index(value)
            self._load_site_data(self.current_site_index)
            
    def _add_site(self):
        if self.current_site_index >= 0:
            self._flush_current_site_changes(silent=True)
            
        new_site = {
            "id": f"new_site_{len(self.sites)}",
            "display_name": "New Website",
            "url": "",
            "username": "",
            "app_password": "",
            "category_map": [],
            "article_templates": {"general": "", "species_profile": "", "comparison": ""}
        }
        self.sites.append(new_site)
        self.current_site_index = len(self.sites) - 1
        self._refresh_site_list()
        
    def _delete_site(self):
        if self.current_site_index >= 0 and self.sites:
            if ask_yes_no("Xác nhận", "Bạn có chắc muốn xóa cấu hình website này?"):
                self.sites.pop(self.current_site_index)
                self._refresh_site_list()
                
    def _load_site_data(self, index):
        if index < 0 or index >= len(self.sites): return
        site = self.sites[index]
        self.site_id_var.set(site.get("id", ""))
        self.site_name_var.set(site.get("display_name", ""))
        self.site_url_var.set(site.get("url", ""))
        self.site_user_var.set(site.get("username", ""))
        self.site_pass_var.set(site.get("app_password", ""))
        
        self.cat_textbox.delete("1.0", "end")
        self.cat_textbox.insert("1.0", json.dumps(site.get("category_map", []), indent=2, ensure_ascii=False))
        
        templates = site.get("article_templates", {})
        if not isinstance(templates, dict):
             templates = {"general": "", "species_profile": "", "comparison": ""}
        self.current_templates = templates.copy()
        
        self.tpl_type_var.set("general")
        self._on_template_type_changed("general")
        self.test_status_label.configure(text="")
        
    def _on_template_type_changed(self, value):
        # First save current template text
        if hasattr(self, 'previous_tpl_type') and self.previous_tpl_type:
            self.current_templates[self.previous_tpl_type] = self.tpl_textbox.get("1.0", "end-1c")
        
        self.tpl_textbox.delete("1.0", "end")
        self.tpl_textbox.insert("1.0", self.current_templates.get(value, ""))
        self.previous_tpl_type = value
        
    def _flush_current_site_changes(self, silent=False):
        if self.current_site_index < 0 or self.current_site_index >= len(self.sites): return
        site = self.sites[self.current_site_index]
        site["id"] = self.site_id_var.get()
        site["display_name"] = self.site_name_var.get()
        site["url"] = self.site_url_var.get()
        site["username"] = self.site_user_var.get()
        site["app_password"] = self.site_pass_var.get()
        
        try:
            cat_json = self.cat_textbox.get("1.0", "end-1c").strip()
            if cat_json:
                site["category_map"] = json.loads(cat_json)
            else:
                site["category_map"] = []
        except Exception as e:
            if not silent:
                show_error("JSON Không Hợp Lệ", f"Định dạng Category Map không đúng JSON.\n{e}")
            
        # Save current active template
        current_tpl = self.tpl_type_var.get()
        self.current_templates[current_tpl] = self.tpl_textbox.get("1.0", "end-1c")
        site["article_templates"] = self.current_templates
        
    def _save_changes(self):
        self._flush_current_site_changes()
        self.settings_manager.set("wp_sites", self.sites)
        show_info("Thành công", "Đã lưu cài đặt WordPress Themes/Sites.")
        self._refresh_site_list()
        
    def _test_connection(self):
        self._flush_current_site_changes()
        if self.current_site_index < 0: return
        site = self.sites[self.current_site_index]
        
        self.test_status_label.configure(text="Đang kiểm tra...", text_color=Colors.WARNING)
        self.update()
        
        try:
            client = WordPressAPIClient(site)
            if client.test_connection():
                self.test_status_label.configure(text="✓ Kết nối thành công!", text_color=Colors.SUCCESS)
        except Exception as e:
             self.test_status_label.configure(text=f"✗ {e}", text_color=Colors.DANGER)
