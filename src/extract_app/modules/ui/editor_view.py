# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/editor_view.py
# Version: 2.0.0
# Description: Dual-pane editor with Dark Navy theme and variant tab support.
# --------------------------------------------------------------------------------

import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Any
from .theme import Colors, Fonts, Spacing


class DualViewEditor(ctk.CTkToplevel):
    """
    A side-by-side editor for Original Text vs Translation.
    Supports switching between Archive / Website / Facebook variants.
    """
    def __init__(self, master, article_data: dict, on_save: Callable[[int, str], None], db_manager=None):
        super().__init__(master)
        self.article_data = article_data
        self.on_save = on_save
        self.db_manager = db_manager
        self.article_id = article_data['id']
        
        title = article_data.get('subtitle', 'Editor')
        self.title(f"Biên tập: {title}")
        self.geometry("1100x750")
        self.configure(fg_color=Colors.BG_APP)
        
        # UI Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # ── Header ──
        self.header = ctk.CTkFrame(self, height=50, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=Spacing.MD, pady=(Spacing.MD, Spacing.SM))
        
        ctk.CTkLabel(
            self.header, text=f"📝 {title[:60]}", 
            font=Fonts.H3, text_color=Colors.TEXT_PRIMARY
        ).pack(side="left", padx=Spacing.LG)
        
        # Save Button
        self.btn_save = ctk.CTkButton(
            self.header, text="💾 Lưu", command=self._save_changes,
            width=80, height=32,
            fg_color=Colors.SUCCESS, text_color=Colors.TEXT_PRIMARY,
            hover_color=Colors.SUCCESS_HOVER, font=Fonts.BODY_BOLD,
            corner_radius=Spacing.BUTTON_RADIUS
        )
        self.btn_save.pack(side="right", padx=Spacing.MD)
        
        # Preview Button
        if self.db_manager:
            self.btn_preview = ctk.CTkButton(
                self.header, text="👁️ Xem Thử", width=90, height=32,
                fg_color=Colors.BG_CARD_HOVER, text_color=Colors.TEXT_SECONDARY,
                hover_color=Colors.BORDER, font=Fonts.BODY,
                corner_radius=Spacing.BUTTON_RADIUS,
                command=self._preview_webview
            )
            self.btn_preview.pack(side="right", padx=Spacing.SM)
        
        # ── Left Panel: Original ──
        self.frame_orig = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS)
        self.frame_orig.grid(row=1, column=0, sticky="nsew", padx=(Spacing.MD, Spacing.XS), pady=Spacing.SM)
        
        ctk.CTkLabel(
            self.frame_orig, text="📄 Văn bản gốc", 
            text_color=Colors.TEXT_MUTED, font=Fonts.SMALL
        ).pack(pady=(Spacing.SM, Spacing.XS), padx=Spacing.MD, anchor="w")
        
        self.txt_orig = ctk.CTkTextbox(
            self.frame_orig, wrap="word", 
            font=("Consolas", 12),
            fg_color=Colors.BG_INPUT, text_color=Colors.TEXT_SECONDARY,
            border_width=1, border_color=Colors.BORDER,
            corner_radius=Spacing.BUTTON_RADIUS
        )
        self.txt_orig.pack(fill="both", expand=True, padx=Spacing.SM, pady=(0, Spacing.SM))
        self.txt_orig.insert("1.0", article_data.get('content_text', ''))
        self.txt_orig.configure(state="disabled")
        
        # ── Right Panel: Translation with variant tabs ──
        self.frame_trans = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS)
        self.frame_trans.grid(row=1, column=1, sticky="nsew", padx=(Spacing.XS, Spacing.MD), pady=Spacing.SM)
        
        # Tab bar for variants
        tab_bar = ctk.CTkFrame(self.frame_trans, fg_color="transparent", height=36)
        tab_bar.pack(fill="x", padx=Spacing.SM, pady=(Spacing.SM, 0))
        
        self.current_variant = "archive"
        self.variant_buttons = {}
        
        variants = [
            ("archive", "📥 Lưu trữ"),
            ("website", "🌐 Website"),
            ("facebook", "📱 Facebook"),
        ]
        
        for var_key, var_label in variants:
            btn = ctk.CTkButton(
                tab_bar, text=var_label, width=90, height=28,
                fg_color=Colors.PRIMARY if var_key == "archive" else "transparent",
                text_color=Colors.TEXT_PRIMARY,
                hover_color=Colors.BG_CARD_HOVER,
                font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                command=lambda k=var_key: self._switch_variant(k)
            )
            btn.pack(side="left", padx=2)
            self.variant_buttons[var_key] = btn
        
        self.txt_trans = ctk.CTkTextbox(
            self.frame_trans, wrap="word",
            font=("Segoe UI", 12),
            fg_color=Colors.BG_INPUT, text_color=Colors.TEXT_PRIMARY,
            border_width=1, border_color=Colors.BORDER_ACCENT,
            corner_radius=Spacing.BUTTON_RADIUS
        )
        self.txt_trans.pack(fill="both", expand=True, padx=Spacing.SM, pady=(Spacing.XS, Spacing.SM))
        self.txt_trans.insert("1.0", article_data.get('translation_text', ''))
        
        # ── Status Bar ──
        self.status_frame = ctk.CTkFrame(self, height=32, fg_color=Colors.BG_CARD, corner_radius=Spacing.BUTTON_RADIUS)
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=Spacing.MD, pady=(0, Spacing.MD))
        
        self.lbl_orig_count = ctk.CTkLabel(
            self.status_frame, text="Gốc: 0 từ", 
            text_color=Colors.TEXT_MUTED, font=Fonts.TINY
        )
        self.lbl_orig_count.pack(side="left", padx=Spacing.LG)
        
        self.lbl_trans_count = ctk.CTkLabel(
            self.status_frame, text="Dịch: 0 từ", 
            text_color=Colors.TEXT_MUTED, font=Fonts.TINY
        )
        self.lbl_trans_count.pack(side="left", padx=Spacing.LG)
        
        self.lbl_status = ctk.CTkLabel(
            self.status_frame, text="", 
            text_color=Colors.SUCCESS, font=Fonts.SMALL
        )
        self.lbl_status.pack(side="right", padx=Spacing.LG)

        # Events
        self.txt_trans.bind("<KeyRelease>", self._update_counts)
        self.txt_trans.focus_set()
        self._update_counts()

    def _switch_variant(self, variant_key: str):
        """Switch between archive/website/facebook text in the editor."""
        # Save current text to memory before switching
        current_text = self.txt_trans.get("1.0", "end-1c")
        if self.current_variant == "archive":
            self.article_data['translation_text'] = current_text
        elif self.current_variant == "website":
            self.article_data['website_text'] = current_text
        elif self.current_variant == "facebook":
            self.article_data['facebook_text'] = current_text
        
        # Update tab button colors
        for key, btn in self.variant_buttons.items():
            if key == variant_key:
                btn.configure(fg_color=Colors.PRIMARY)
            else:
                btn.configure(fg_color="transparent")
        
        # Load the selected variant
        self.current_variant = variant_key
        text_map = {
            "archive": self.article_data.get('translation_text', ''),
            "website": self.article_data.get('website_text', ''),
            "facebook": self.article_data.get('facebook_text', ''),
        }
        new_text = text_map.get(variant_key, '') or ''
        
        self.txt_trans.delete("1.0", "end")
        self.txt_trans.insert("1.0", new_text)
        
        # Update border color to indicate variant
        border_map = {
            "archive": Colors.BORDER_ACCENT,
            "website": Colors.PRIMARY,
            "facebook": Colors.WARNING,
        }
        self.txt_trans.configure(border_color=border_map.get(variant_key, Colors.BORDER))
        self._update_counts()

    def _update_counts(self, event=None):
        """Updates word counts for both text areas."""
        orig_text = self.txt_orig.get("1.0", "end-1c")
        orig_count = len(orig_text.split()) if orig_text else 0
        self.lbl_orig_count.configure(text=f"Gốc: {orig_count:,} từ")
        
        trans_text = self.txt_trans.get("1.0", "end-1c")
        trans_count = len(trans_text.split()) if trans_text else 0
        self.lbl_trans_count.configure(text=f"Dịch: {trans_count:,} từ")

    def _save_changes(self):
        new_text = self.txt_trans.get("1.0", "end-1c")
        try:
            if self.current_variant == "archive":
                self.on_save(self.article_id, new_text)
            elif self.db_manager:
                self.db_manager.update_article_variant(self.article_id, self.current_variant, new_text)
            
            label_map = {"archive": "Lưu trữ", "website": "Website", "facebook": "Facebook"}
            label = label_map.get(self.current_variant, "")
            self.lbl_status.configure(
                text=f"✅ Đã lưu {label} lúc {self._get_time_str()}", 
                text_color=Colors.SUCCESS
            )
            self.after(3000, lambda: self.lbl_status.configure(text=""))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")
            
    def _preview_webview(self):
        """Generates a temporary webview for this article."""
        if not self.db_manager:
            return
            
        try:
            import webbrowser
            from pathlib import Path
            import shutil
            from ...core import webview_generator
            
            current_trans = self.txt_trans.get("1.0", "end-1c")
            current_orig = self.txt_orig.get("1.0", "end-1c")
            
            preview_chapters = [{
                'title': 'Preview',
                'articles': [{
                    'subtitle': self.article_data.get('subtitle', 'Preview Article'),
                    'content_text': current_orig,
                    'translation_text': current_trans
                }]
            }]
            
            output_dir = Path("user_data/webview_preview")
            
            if output_dir.exists():
                try:
                     shutil.rmtree(output_dir)
                except:
                     pass
            
            index_path = webview_generator.generate_webview(
                "Preview Mode", "Editor", preview_chapters, output_dir
            )
            
            real_images_dir = output_dir / "images"
            real_images_dir.mkdir(parents=True, exist_ok=True)
            
            images = self.db_manager.get_article_images(self.article_id)
            for img in images:
                src_path = Path(img['path'])
                if src_path.exists():
                    dest_path = real_images_dir / src_path.name
                    if not dest_path.exists():
                        shutil.copy2(src_path, dest_path)
            
            webbrowser.open(index_path.resolve().as_uri())

        except Exception as e:
            messagebox.showerror("Lỗi Preview", f"Không thể tạo preview: {e}")
            print(e)
            
    def _get_time_str(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
