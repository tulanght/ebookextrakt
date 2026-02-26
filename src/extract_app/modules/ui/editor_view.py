
import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Any

class DualViewEditor(ctk.CTkToplevel):
    """
    A side-by-side editor for Original Text vs Translation.
    Functions:
    - View original
    - Edit translation
    - Save changes to DB
    """
    def __init__(self, master, article_data: dict, on_save: Callable[[int, str], None], db_manager=None):
        super().__init__(master)
        self.article_data = article_data
        self.on_save = on_save
        self.db_manager = db_manager
        self.article_id = article_data['id']
        
        title = article_data.get('subtitle', 'Editor')
        self.title(f"Biên tập: {title}")
        self.geometry("1000x700")
        
        # UI Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self.header = ctk.CTkFrame(self, height=50)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.header, text=title, font=("Segoe UI", 16, "bold")).pack(side="left", padx=10)
        
        # Buttons: Save & Preview
        self.btn_save = ctk.CTkButton(self.header, text="💾 Lưu Thay Đổi", command=self._save_changes)
        self.btn_save.pack(side="right", padx=10)
        
        if self.db_manager:
            self.btn_preview = ctk.CTkButton(self.header, text="👁️ Xem Thử", width=100, fg_color="gray", command=self._preview_webview)
            self.btn_preview.pack(side="right", padx=10)
        
        # Content Area
        # Left: Original
        self.frame_orig = ctk.CTkFrame(self)
        self.frame_orig.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        ctk.CTkLabel(self.frame_orig, text="Gốc (Không thể sửa)", text_color="gray").pack(pady=5)
        self.txt_orig = ctk.CTkTextbox(self.frame_orig, wrap="word", font=("Consolas", 12))
        self.txt_orig.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_orig.insert("1.0", article_data.get('content_text', ''))
        self.txt_orig.configure(state="disabled")
        
        # Right: Translation
        self.frame_trans = ctk.CTkFrame(self)
        self.frame_trans.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        ctk.CTkLabel(self.frame_trans, text="Bản Dịch (Có thể sửa)", text_color="gray").pack(pady=5)
        self.txt_trans = ctk.CTkTextbox(self.frame_trans, wrap="word", font=("Segoe UI", 12))
        self.txt_trans.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_trans.insert("1.0", article_data.get('translation_text', ''))
        
        # Status Bar / Metrics
        self.status_frame = ctk.CTkFrame(self, height=30)
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        self.lbl_orig_count = ctk.CTkLabel(self.status_frame, text="Original: 0 words", text_color="gray", font=("Segoe UI", 11))
        self.lbl_orig_count.pack(side="left", padx=10)
        
        self.lbl_trans_count = ctk.CTkLabel(self.status_frame, text="Translation: 0 words", text_color="gray", font=("Segoe UI", 11))
        self.lbl_trans_count.pack(side="left", padx=10)
        
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="", text_color="green", font=("Segoe UI", 11, "bold"))
        self.lbl_status.pack(side="right", padx=10)

        # Focus
        self.txt_trans.bind("<KeyRelease>", self._update_counts)
        self.txt_trans.focus_set()
        
        # Initial Count
        self._update_counts()

    def _update_counts(self, event=None):
        """Updates word counts for both text areas."""
        # Original
        orig_text = self.txt_orig.get("1.0", "end-1c")
        orig_count = len(orig_text.split()) if orig_text else 0
        self.lbl_orig_count.configure(text=f"Original: {orig_count:,} words")
        
        # Translation
        trans_text = self.txt_trans.get("1.0", "end-1c")
        trans_count = len(trans_text.split()) if trans_text else 0
        self.lbl_trans_count.configure(text=f"Translation: {trans_count:,} words")

    def _save_changes(self):
        new_trans = self.txt_trans.get("1.0", "end-1c")
        try:
            self.on_save(self.article_id, new_trans)
            # Show ephemeral success status instead of popup to keep flow smooth
            self.lbl_status.configure(text="✅ Đã lưu lúc " + self._get_time_str(), text_color="green")
            # Auto-clear status after 3 seconds
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
            
            # Use current text from editor, not DB
            current_trans = self.txt_trans.get("1.0", "end-1c")
            current_orig = self.txt_orig.get("1.0", "end-1c")
            
            # Prepare data
            preview_chapters = [{
                'title': 'Preview',
                'articles': [{
                    'subtitle': self.article_data.get('subtitle', 'Preview Article'),
                    'content_text': current_orig,
                    'translation_text': current_trans
                }]
            }]
            
            # Folder setup
            output_dir = Path("user_data/webview_preview")
            images_dir = output_dir / "webview" / "images" # webview_generator creates 'webview' subdir
            
            # Cleanup old preview
            if output_dir.exists():
                try:
                     shutil.rmtree(output_dir)
                except:
                     pass
            
            # Generate Webview
            index_path = webview_generator.generate_webview(
                "Preview Mode", "Editor", preview_chapters, output_dir
            )
            
            # Copy Images
            # We need to create the images dir inside 'webview' because that's where html looks: ../images/
            # Wait, generator structure:
            # webview/index.html
            # webview/css
            # webview/js
            # logic in js: src="../images/file" -> It expects images to be SIBLING of webview folder?
            # Let's check js: `src="../images/${file}"`
            # So if index is at `webview/index.html`, `../images` means `output_dir/images`.
            
            real_images_dir = output_dir / "images"
            real_images_dir.mkdir(parents=True, exist_ok=True)
            
            images = self.db_manager.get_article_images(self.article_id)
            for img in images:
                src_path = Path(img['path'])
                if src_path.exists():
                    dest_path = real_images_dir / src_path.name
                    if not dest_path.exists():
                        shutil.copy2(src_path, dest_path)
            
            # Open
            webbrowser.open(index_path.resolve().as_uri())

        except Exception as e:
            messagebox.showerror("Lỗi Preview", f"Không thể tạo preview: {e}")
            print(e)
            
    def _get_time_str(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
