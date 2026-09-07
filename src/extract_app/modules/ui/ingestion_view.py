# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/ingestion_view.py
# Version: 1.6.0
# Author: Antigravity
# Description: Ebook Manager View with AI Standardization, Queue & Fast Ingest
# --------------------------------------------------------------------------------

import customtkinter as ctk
from customtkinter import filedialog
from typing import Any, List, Dict
import os
import shutil
import threading
import queue
from pathlib import Path
from .theme import Colors, Fonts, Spacing
from src.extract_app.core.ai_classifier import AIClassifier
from src.extract_app.core.config import get_user_data_dir
from src.extract_app.shared.debug_logger import log as global_log
import tkinter as tk
import sys

project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from scripts.organize_ebooks import classify_file, load_overrides, INBOX_ROOT
from send2trash import send2trash

class IngestionView(ctk.CTkFrame):
    def __init__(self, master, db_manager, cloud_client, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db_manager = db_manager
        self.cloud_client = cloud_client
        self.ai_classifier = AIClassifier(cloud_client)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.scanned_files: List[Dict[str, Any]] = []
        self.duplicate_groups: Dict[int, List[Dict[str, Any]]] = {}
        self.clean_files: List[Dict[str, Any]] = []
        self.db_duplicates: List[Dict[str, Any]] = []
        self.selected_source_dir = ""
        self._cancel_scan = False
        
        # Hàng đợi & Worker Threads
        self.task_queue = queue.Queue()
        self._start_workers(2)  # Cấu hình 2 worker chạy ngầm song song
        
        # Use physical Ebooks root
        self.lib_dir = INBOX_ROOT
            
        self._init_header()
        self._init_controls()
        self._init_main_content()

    def _start_workers(self, num_workers):
        for _ in range(num_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            
    def _worker_loop(self):
        while True:
            task = self.task_queue.get()
            try:
                task()
            except Exception as e:
                print(f"[Worker Error] {e}")
            finally:
                self.task_queue.task_done()
        
    def _init_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS)
        header_frame.grid(row=0, column=0, sticky="ew", padx=Spacing.LG, pady=(Spacing.LG, Spacing.SM))
        lbl_title = ctk.CTkLabel(header_frame, text="📚 Quản lý Kho Ebook Gốc", font=Fonts.H2)
        lbl_title.pack(side="left", padx=Spacing.LG, pady=Spacing.MD)

    def _init_controls(self):
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.grid(row=1, column=0, sticky="ew", padx=Spacing.LG, pady=(0, Spacing.SM))
        
        self.btn_select_dir = ctk.CTkButton(
            ctrl_frame, text="📂 Nhập Kho", font=Fonts.BUTTON, 
            command=self._select_directory, width=120
        )
        self.btn_select_dir.pack(side="left", padx=(0, Spacing.MD))
        
        self.btn_scan = ctk.CTkButton(
            ctrl_frame, text="🔍 Bắt đầu Quét", font=Fonts.BUTTON, 
            command=self._scan_and_dedup, fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER,
            state="disabled", width=120
        )
        self.btn_scan.pack(side="left")
        
        self.lbl_dir = ctk.CTkLabel(ctrl_frame, text="", text_color=Colors.TEXT_MUTED)
        self.lbl_dir.pack(side="left", padx=Spacing.MD)
        
        btn_refresh = ctk.CTkButton(
            ctrl_frame, text="🔄 Làm mới Kho", font=Fonts.BUTTON, 
            command=self._load_dashboard_data, width=120, fg_color=Colors.BG_CARD
        )
        btn_refresh.pack(side="right", padx=Spacing.MD)
        
        self.btn_batch_clean = ctk.CTkButton(
            ctrl_frame, text="🧹 Dọn dẹp File Rác", font=Fonts.BUTTON,
            command=self._batch_clean, width=150, fg_color=Colors.WARNING, hover_color="#D97706"
        )
        self.btn_batch_clean.pack(side="right")

    def _init_main_content(self):
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.grid(row=2, column=0, sticky="nsew", padx=Spacing.LG, pady=(0, Spacing.LG))
        
        self.ingestion_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.dashboard_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.dashboard_frame.pack(fill="both", expand=True, pady=Spacing.MD)
        
        self._load_dashboard_data()

    def _select_directory(self):
        dir_path = filedialog.askdirectory(title="Chọn thư mục chứa Ebooks")
        if dir_path:
            self.selected_source_dir = dir_path
            self.lbl_dir.configure(text=f"...{dir_path[-30:]}" if len(dir_path) > 30 else dir_path)
            self.btn_scan.configure(state="normal", text="🔍 Bắt đầu Quét", fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER)
            
            self.ingestion_frame.pack(fill="x", pady=Spacing.MD, before=self.dashboard_frame)
            self._clear_ingestion_results()
            ctk.CTkLabel(
                self.ingestion_frame, 
                text="Quy trình Nhập liệu đã sẵn sàng. Bấm 'Bắt đầu Quét' để tiếp tục.",
                text_color=Colors.TEXT_MUTED, font=Fonts.BODY
            ).pack(pady=Spacing.LG)

    def _clear_ingestion_results(self):
        for widget in self.ingestion_frame.winfo_children():
            widget.destroy()

    def _get_dynamic_categories(self):
        cats = []
        bio_dir = self.lib_dir / "Biology"
        if bio_dir.exists():
            for d in bio_dir.iterdir():
                if d.is_dir():
                    cats.append({"id": f"Biology/{d.name}", "name": f"Sinh học: {d.name}", "desc": "Kho sinh học", "path": d})
        
        not_bio = self.lib_dir / "_Review_Not_Biology"
        if not_bio.exists(): cats.append({"id": "_Review_Not_Biology", "name": "Not Biology", "desc": "Cần xem lại", "path": not_bio})
        
        unclass = self.lib_dir / "_UNCLASSIFIED"
        if unclass.exists(): cats.append({"id": "_UNCLASSIFIED", "name": "Chưa phân loại", "desc": "Kho chung", "path": unclass})
        
        return cats

    def _load_dashboard_data(self):
        for widget in self.dashboard_frame.winfo_children():
            widget.destroy()
            
        self.dashboard_frame.grid_columnconfigure((0, 1), weight=1)
            
        all_books = self.db_manager.get_all_books()
        db_path_map = {Path(b['source_path']).resolve(): b for b in all_books if b.get('source_path')}
        
        dynamic_cats = self._get_dynamic_categories()
        
        row_idx = 0
        col_idx = 0
        for cat in dynamic_cats:
            cat_path = cat["path"]
            files = [f for f in cat_path.iterdir() if f.is_file() and f.suffix.lower() in ['.pdf', '.epub']] if cat_path.exists() else []
            
            card = self._create_category_card(self.dashboard_frame, cat, cat_path, files, db_path_map)
            card.grid(row=row_idx, column=col_idx, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)
            
            col_idx += 1
            if col_idx > 1:
                col_idx = 0
                row_idx += 2
                
    def _create_category_card(self, parent, cat, path, files, db_path_map):
        card = ctk.CTkFrame(parent, fg_color=Colors.BG_APP, border_width=1, border_color=Colors.BORDER)
        
        lbl_name = ctk.CTkLabel(card, text=cat['name'], font=Fonts.H3, text_color=Colors.TEXT_PRIMARY)
        lbl_name.pack(anchor="w", padx=Spacing.LG, pady=(Spacing.LG, 0))
        
        lbl_desc = ctk.CTkLabel(card, text=cat['desc'], font=Fonts.SMALL, text_color=Colors.TEXT_MUTED)
        lbl_desc.pack(anchor="w", padx=Spacing.LG)
        
        lbl_count = ctk.CTkLabel(card, text=f"{len(files)} files", font=Fonts.BODY_BOLD, text_color=Colors.PRIMARY)
        lbl_count.pack(anchor="w", padx=Spacing.LG, pady=(Spacing.SM, 0))
        
        act_frame = ctk.CTkFrame(card, fg_color="transparent")
        act_frame.pack(fill="x", padx=Spacing.LG, pady=Spacing.LG)
        
        btn_open = ctk.CTkButton(act_frame, text="Mở thư mục", width=100, command=lambda: os.startfile(str(path)))
        btn_open.pack(side="left")
        
        btn_view = ctk.CTkButton(act_frame, text="Xem chi tiết ⬇", width=100, command=lambda c=card, f=files, db=db_path_map, cid=cat['id']: self._toggle_details(c, f, db, cid))
        btn_view.pack(side="right")
        
        card._details_frame = None
        return card
        
    def _toggle_details(self, card, files, db_path_map, current_cat_id):
        if card._details_frame is not None:
            card._details_frame.destroy()
            card._details_frame = None
            return
            
        info = card.grid_info()
        row, col = info['row'], info['column']
        
        details = ctk.CTkFrame(self.dashboard_frame, fg_color=Colors.BG_INPUT)
        details.grid(row=row+1, column=col, sticky="nsew", padx=Spacing.MD, pady=(0, Spacing.MD))
        card._details_frame = details
        
        if not files:
            ctk.CTkLabel(details, text="Kho trống").pack(pady=Spacing.SM)
            return
            
        for f in files:
            f_row = ctk.CTkFrame(details, fg_color="transparent")
            f_row.pack(fill="x", padx=Spacing.MD, pady=Spacing.XS)
            
            b_info = db_path_map.get(f.resolve())
            db_status = "✅ Đã Ingest" if b_info else "⚠️ Chưa Ingest"
            status_color = Colors.SUCCESS if b_info else Colors.WARNING
            
            display_name = f.name[:45] + '...' if len(f.name) > 45 else f.name
            ctk.CTkLabel(f_row, text=display_name, font=Fonts.BODY, anchor="w").pack(side="left")
            
            actions_frame = ctk.CTkFrame(f_row, fg_color="transparent")
            actions_frame.pack(side="right")
            
            ctk.CTkLabel(actions_frame, text=db_status, font=Fonts.BODY, text_color=status_color).pack(side="left", padx=Spacing.SM)
            
            is_dirty = ('z-lib' in f.name.lower() or '1lib' in f.name.lower() or '_1' in f.name.lower())
            btn_clean = ctk.CTkButton(actions_frame, text="✨ Chuẩn hóa AI" if is_dirty else "🔄 AI Phân loại lại", width=100, height=24, fg_color=Colors.SUCCESS if is_dirty else Colors.PRIMARY,
                                    command=lambda p=f.resolve(), b=b_info, r=f_row: self._clean_single_file(p, b, r))
            btn_clean.pack(side="left", padx=2)
            
            btn_move = ctk.CTkButton(actions_frame, text="🔄 Đổi Kho", width=70, height=24, fg_color=Colors.PRIMARY,
                                    command=lambda p=f.resolve(), b=b_info, r=f_row: self._show_move_menu(p, b, r))
            btn_move.pack(side="left", padx=2)
            
            if b_info:
                btn_del = ctk.CTkButton(actions_frame, text="🗑️ Gỡ bỏ", width=70, height=24, fg_color=Colors.DANGER, hover_color=Colors.DANGER_HOVER,
                                        command=lambda b_id=b_info['id'], p=f.resolve(), r=f_row: self._remove_and_quarantine(b_id, p, r))
                btn_del.pack(side="left", padx=2)

    def _show_move_menu(self, file_path: Path, db_info, row_widget):
        menu = tk.Menu(self, tearoff=0)
        dynamic_cats = self._get_dynamic_categories()
        for cat in dynamic_cats:
            menu.add_command(label=f"Chuyển sang: {cat['name']}", command=lambda cid=cat['id'], p=file_path, b=db_info, rw=row_widget: self._move_file_and_ingest(cid, p, b, rw))
        
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        menu.tk_popup(x, y)
        
    def _move_file_and_ingest(self, target_cat_id: str, file_path: Path, db_info, row_widget):
        for child in row_widget.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for btn in child.winfo_children():
                    if isinstance(btn, ctk.CTkButton) and "Đổi Kho" in btn.cget("text"):
                        btn.configure(text="⏳ Xếp hàng...", state="disabled")
        self.task_queue.put(lambda: self._manual_ingest_worker(target_cat_id, file_path, db_info))

    def _manual_ingest_worker(self, target_cat_id, file_path: Path, db_info):
        try:
            ext = file_path.suffix.lower().replace('.', '')
            text_sample = self._get_sample_text(str(file_path), ext)
            meta = self.ai_classifier.analyze_book(text_sample) if text_sample else {}
            
            extracted_title = (meta.get('title') or '').strip() or file_path.stem
            safe_title = "".join(c for c in extracted_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not safe_title: safe_title = file_path.stem
            
            global_log(f"[MANUAL INGEST] Bắt đầu di chuyển: {file_path.name} -> {safe_title}")
            
            target_dir = self.lib_dir / target_cat_id
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / f"{safe_title}{file_path.suffix}"
            counter = 1
            while target_path.exists() and target_path.resolve() != file_path.resolve():
                target_path = target_dir / f"{safe_title}_{counter}{file_path.suffix}"
                counter += 1
                
            shutil.move(str(file_path), str(target_path))
            category_name = target_cat_id.replace("Biology/", "") if "Biology/" in target_cat_id else target_cat_id
            
            if db_info:
                conn = self.db_manager._get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE books SET title = ?, author = ?, published_year = ?, source_path = ?, category = ? WHERE id = ?", 
                               (meta.get('title', safe_title), meta.get('author', ''), str(meta.get('year', '')), str(target_path.absolute()), category_name, db_info['id']))
                conn.commit()
            else:
                self.db_manager.save_book_batch(
                    book_title=meta.get('title', safe_title),
                    author=meta.get('author', 'Không rõ'),
                    source_path=str(target_path.absolute()),
                    cover_path='', 
                    structured_content=[], 
                    published_year=str(meta.get('year', '')),
                    category=category_name
                )
            self.after(0, self._load_dashboard_data)
        except Exception as e:
            print(f"Lỗi Ingest Thủ công: {e}")

    def _clean_single_file(self, file_path: Path, db_info, row_widget):
        for child in row_widget.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for btn in child.winfo_children():
                    if isinstance(btn, ctk.CTkButton) and "Chuẩn hóa AI" in btn.cget("text"):
                        btn.configure(text="⏳ Xếp hàng...", state="disabled")
        self.task_queue.put(lambda: self._clean_single_worker(file_path, db_info))

    def _clean_single_worker(self, file_path: Path, db_info: Any) -> None:
        """Normalize, classify, and move one ebook from a background worker."""

        try:
            ext = file_path.suffix.lower().replace('.', '')
            text_sample = self._get_sample_text(str(file_path), ext)
            meta = self.ai_classifier.analyze_book(text_sample, file_path.name)

            extracted_title = (meta.get('title') or '').strip() or file_path.stem
            author = (meta.get('author') or '').strip()

            if author and author.lower() != 'không rõ':
                full_name = f"{extracted_title} - {author}"
            else:
                full_name = extracted_title

            safe_title = "".join(c for c in full_name if c.isalnum() or c in (' ', '-', '_', '.', ',')).rstrip()
            if not safe_title: safe_title = file_path.stem

            overrides = load_overrides()
            cat_folder = classify_file(safe_title, overrides)

            if cat_folder == "_NOT_BIOLOGY":
                target_dir = self.lib_dir / "_Review_Not_Biology"
            elif cat_folder == "_UNCLASSIFIED":
                target_dir = self.lib_dir / "_UNCLASSIFIED"
            elif cat_folder == "_SKIP":
                target_dir = self.lib_dir / "_SKIP"
            else:
                target_dir = self.lib_dir / "Biology" / cat_folder

            target_dir.mkdir(parents=True, exist_ok=True)

            # Physical duplicate check
            target_file_name = f"{safe_title}{file_path.suffix}"
            source_path = file_path.resolve()
            duplicate_path = None
            for existing in self.lib_dir.rglob(target_file_name):
                if existing.resolve() != source_path:
                    duplicate_path = existing
                    break

            if duplicate_path is not None:
                if db_info:
                    message = (
                        f"[CẦN ĐỐI SOÁT] Giữ nguyên file đã đăng ký DB: "
                        f"{file_path.name}. Bản vật lý khác: {duplicate_path}."
                    )
                    global_log(message)
                    self._safe_log(message)
                    self.after(0, self._load_dashboard_data)
                    return

                global_log(
                    f"  -> [BỎ QUA] Đã tồn tại bản khác: {duplicate_path}. "
                    "Chuyển file nguồn vào Thùng rác."
                )
                self._quarantine_file(str(file_path))
                self.after(0, self._load_dashboard_data)
                return

            target_path = target_dir / target_file_name
            if target_path.resolve() != source_path:
                counter = 1
                while target_path.exists():
                    target_path = target_dir / f"{safe_title}_{counter}{file_path.suffix}"
                    counter += 1
                shutil.move(str(file_path), str(target_path))
            else:
                target_path = source_path
            category_name = cat_folder
            
            global_log(f"[AI ROUTING] {file_path.name} -> {target_path.absolute()}")
            
            if db_info:
                conn = self.db_manager._get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE books SET title = ?, author = ?, published_year = ?, source_path = ?, category = ? WHERE id = ?", 
                               (meta.get('title', safe_title), meta.get('author', ''), str(meta.get('year', '')), str(target_path.absolute()), category_name, db_info['id']))
                conn.commit()
            else:
                self.db_manager.save_book_batch(
                    book_title=meta.get('title', safe_title),
                    author=meta.get('author', 'Không rõ'),
                    source_path=str(target_path.absolute()),
                    cover_path='',
                    structured_content=[], 
                    published_year=str(meta.get('year', '')),
                    category=category_name
                )
            self.after(0, self._load_dashboard_data)
        except Exception as e:
            print(f"Lỗi AI Clean Single: {e}")

    def _batch_clean(self):
        self.btn_batch_clean.configure(state="disabled", text="⏳ Đã đưa vào Hàng đợi...")
        self.task_queue.put(self._batch_clean_worker)

    def _batch_clean_worker(self):
        all_books = self.db_manager.get_all_books()
        db_path_map = {Path(b['source_path']).resolve(): b for b in all_books if b.get('source_path')}

        dynamic_cats = self._get_dynamic_categories()
        for cat in dynamic_cats:
            cat_path = cat["path"]
            if not cat_path.exists(): continue
            for f in cat_path.iterdir():
                if f.is_file() and f.suffix.lower() in ['.pdf', '.epub', '.mobi', '.azw3']:
                    is_dirty = ('z-lib' in f.name.lower() or '1lib' in f.name.lower() or '_1' in f.name.lower())
                    if is_dirty:
                        self._clean_single_worker(f.resolve(), db_path_map.get(f.resolve()))
                        
        self.after(0, lambda: self.btn_batch_clean.configure(state="normal", text="🧹 Dọn dẹp File Rác"))
        self.after(0, self._load_dashboard_data)

    def _remove_and_quarantine(
        self,
        book_id: int,
        file_path: Path,
        row_widget: Any,
    ) -> None:
        """Recycle an ebook before removing its database catalog record."""
        connection = None
        try:
            send2trash(str(file_path))

            connection = self.db_manager._get_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            connection.commit()

            row_widget.destroy()
            self.after(500, self._load_dashboard_data)
        except Exception as e:
            if connection is not None:
                connection.rollback()
            print(f"Lỗi khi Xóa sách: {e}")

    def _handle_scan_btn_click(self):
        if self.btn_scan.cget("text") == "🛑 Dừng Lại":
            self._cancel_scan = True
            self.btn_scan.configure(state="disabled", text="Đang dừng...")
        else:
            self._scan_and_dedup()

    def _scan_and_dedup(self):
        if not self.selected_source_dir: return
        self._cancel_scan = False
        self.btn_scan.configure(command=self._handle_scan_btn_click)
        self.btn_scan.configure(text="🛑 Dừng Lại", fg_color=Colors.DANGER, hover_color=Colors.DANGER_HOVER)
        self._clear_ingestion_results()
        
        self.scan_log = ctk.CTkTextbox(
            self.ingestion_frame, height=200, fg_color=Colors.BG_INPUT, text_color=Colors.TEXT_PRIMARY
        )
        self.scan_log.pack(fill="x", pady=Spacing.MD)
        self.scan_log.insert("end", "Bắt đầu quét thư mục...\n")
        self.update()
        
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _safe_log(self, msg: str):
        self.after(0, lambda: self._insert_log(msg))
        
    def _insert_log(self, msg: str):
        if hasattr(self, 'scan_log') and self.scan_log.winfo_exists():
            self.scan_log.insert("end", msg + "\n")
            self.scan_log.see("end")

    def _safe_ai_log(self, msg: str):
        self.after(0, lambda: self._insert_ai_log(msg))
        
    def _insert_ai_log(self, msg: str):
        if hasattr(self, 'ai_log') and self.ai_log.winfo_exists():
            self.ai_log.insert("end", msg + "\n")
            self.ai_log.see("end")

    def _scan_worker(self):
        self.scanned_files = []
        self.db_duplicates = []
        files_scanned = 0
        
        try:
            all_books = self.db_manager.get_all_books()
            known_filenames = {}
            for b in all_books:
                path = b.get('source_path', '')
                if path:
                    known_filenames[os.path.basename(path).lower()] = b
                    
            dynamic_cats = self._get_dynamic_categories()
            for cat in dynamic_cats:
                cat_path = cat["path"]
                if cat_path.exists():
                    for existing_f in cat_path.iterdir():
                        if existing_f.is_file() and existing_f.name.lower() not in known_filenames:
                            known_filenames[existing_f.name.lower()] = {'title': existing_f.stem, 'source_path': str(existing_f.absolute())}
                            
            self._safe_log(f"Đã nạp {len(known_filenames)} sách từ hệ thống để đối chiếu trùng lặp.")
            
            for root, _, files in os.walk(self.selected_source_dir):
                if self._cancel_scan: break
                for file in files:
                    if self._cancel_scan: break
                    ext = file.lower().split('.')[-1]
                    if ext in ['pdf', 'epub', 'mobi', 'azw3']:
                        full_path = os.path.join(root, file)
                        size = os.path.getsize(full_path)
                        f_info = {
                            'name': file,
                            'path': full_path,
                            'size': size,
                            'ext': ext
                        }
                        
                        if file.lower() in known_filenames:
                            f_info['db_match'] = known_filenames[file.lower()]
                            self.db_duplicates.append(f_info)
                            self._safe_log(f"[DB TRÙNG] {file}")
                        else:
                            self.scanned_files.append(f_info)
                            self._safe_log(f"[QUÉT] {file}")
                            
                        files_scanned += 1
                        
        except Exception as e:
            self._safe_log(f"Lỗi khi quét: {e}")
            self.after(0, self._reset_scan_btn)
            return
            
        if self._cancel_scan:
            self._safe_log("\n[!] Đã dừng quét bởi người dùng.")
            self.after(0, self._reset_scan_btn)
            return
                    
        size_groups = {}
        for f in self.scanned_files:
            size_groups.setdefault(f['size'], []).append(f)
            
        self.duplicate_groups = {s: files for s, files in size_groups.items() if len(files) > 1}
        self.after(0, self._finish_scan)
        
    def _reset_scan_btn(self):
        self.btn_scan.configure(command=self._scan_and_dedup)
        self.btn_scan.configure(state="normal", text="🔍 Quét lại", fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER)

    def _finish_scan(self):
        self._reset_scan_btn()
        self._render_results()

    def _render_results(self):
        total = len(self.scanned_files) + len(self.db_duplicates)
        dupes = sum(len(g) for g in self.duplicate_groups.values())
        db_dupes = len(self.db_duplicates)
        
        summary = ctk.CTkLabel(
            self.ingestion_frame, 
            text=f"Đã quét {total} files. Phát hiện: {db_dupes} trùng Thư viện, {dupes} trùng nội bộ.",
            font=Fonts.H3, text_color=Colors.SUCCESS if (dupes == 0 and db_dupes == 0) else Colors.WARNING,
            justify="left"
        )
        summary.pack(anchor="w", padx=Spacing.MD, pady=Spacing.MD)
        
        if db_dupes > 0 or dupes > 0:
            btn_del_all = ctk.CTkButton(self.ingestion_frame, text="🗑️ Xóa tất cả trùng lặp", font=Fonts.BUTTON, fg_color=Colors.DANGER, hover_color=Colors.DANGER_HOVER, command=self._delete_all_duplicates)
            btn_del_all.pack(anchor="w", padx=Spacing.MD, pady=(0, Spacing.MD))
        
        if db_dupes > 0:
            db_frame = ctk.CTkFrame(self.ingestion_frame, fg_color=Colors.BG_APP, border_width=1, border_color=Colors.WARNING)
            db_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
            ctk.CTkLabel(db_frame, text=f"📚 Trùng lặp với Thư viện Database ({db_dupes} files)", font=Fonts.BODY_BOLD, text_color=Colors.WARNING).pack(anchor="w", padx=Spacing.MD, pady=(Spacing.SM, 0))
            for i, f in enumerate(self.db_duplicates):
                f_frame = ctk.CTkFrame(db_frame, fg_color="transparent")
                f_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.XS)
                ctk.CTkLabel(f_frame, text=f"{f['name']}", font=Fonts.BODY).pack(side="left")
                ctk.CTkButton(f_frame, text="🗑️ Xóa", width=60, fg_color=Colors.DANGER, height=24, command=lambda path=f['path'], row_w=f_frame: self._quarantine_file(path, row_w)).pack(side="right", padx=Spacing.SM)
                
        for size, files in self.duplicate_groups.items():
            group_frame = ctk.CTkFrame(self.ingestion_frame, fg_color=Colors.BG_APP, border_width=1, border_color=Colors.DANGER)
            group_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
            size_mb = round(size / (1024*1024), 2)
            ctk.CTkLabel(group_frame, text=f"⚠️ Trùng lặp nội bộ thư mục ({size_mb} MB)", font=Fonts.BODY_BOLD, text_color=Colors.DANGER).pack(anchor="w", padx=Spacing.MD, pady=(Spacing.SM, 0))
            for i, f in enumerate(files):
                f_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
                f_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.XS)
                ctk.CTkLabel(f_frame, text=f"{f['name']}", font=Fonts.BODY).pack(side="left")
                ctk.CTkButton(f_frame, text="🗑️ Xóa", width=60, fg_color=Colors.DANGER, height=24, command=lambda path=f['path'], row_w=f_frame: self._quarantine_file(path, row_w)).pack(side="right", padx=Spacing.SM)
                
        self._render_ai_step()
        
    def _quarantine_file(
        self,
        file_path: str | Path,
        widget: Any = None,
    ) -> bool:
        """Move a file to Recycle Bin and dispatch UI effects to Tk's thread."""
        try:
            p = Path(file_path)
            clean_path = str(p).replace('/', '\\')
            if clean_path.startswith('\\\\?\\'):
                clean_path = clean_path[4:]
            try:
                send2trash(clean_path)
            except Exception as trash_error:
                self._safe_log(
                    f"[LỖI XÓA] Không thể chuyển vào Thùng rác; "
                    f"file được giữ nguyên: {p.name} ({trash_error})"
                )
                return False

            if widget:
                self.after(0, widget.destroy)
            self._safe_log(f"[XÓA] Đã xử lý file rác: {p.name}")
            return True
        except Exception as e:
            self._safe_log(f"[LỖI XÓA] {e}")
            return False

    def _delete_all_duplicates(self):
        for f in self.db_duplicates:
            self._quarantine_file(f['path'])
        for files in self.duplicate_groups.values():
            for f in files:
                self._quarantine_file(f['path'])
        self.db_duplicates = []
        self.duplicate_groups = {}
        self._clear_ingestion_results()
        self._render_results()

    def _render_ai_step(self):
        unique_sizes = {}
        for f in self.scanned_files:
            if f['size'] not in unique_sizes:
                unique_sizes[f['size']] = f
        self.clean_files = list(unique_sizes.values())
        
        if not self.clean_files:
            return 
            
        frame_ai = ctk.CTkFrame(self.ingestion_frame, fg_color=Colors.BG_CARD)
        frame_ai.pack(fill="x", padx=Spacing.MD, pady=Spacing.XL)
        
        ctk.CTkLabel(
            frame_ai, text=f"🎉 Sẵn sàng phân loại AI cho {len(self.clean_files)} sách sạch.", 
            text_color=Colors.SUCCESS, font=Fonts.BODY_BOLD
        ).pack(pady=Spacing.MD)
        
        self.btn_ai = ctk.CTkButton(
            frame_ai, text="✨ Bắt đầu Phân loại & Sửa Metadata (Vertex AI)", font=Fonts.BUTTON,
            command=self._handle_ai_btn_click
        )
        self.btn_ai.pack(pady=(0, Spacing.MD))
        
        self.ai_log = ctk.CTkTextbox(frame_ai, height=250, fg_color=Colors.BG_INPUT)
        self.ai_log.pack(fill="x", padx=Spacing.MD, pady=Spacing.MD)

    def _get_sample_text(self, file_path: str, ext: str, limit: int = 15000) -> str:
        text = ""
        try:
            if ext == 'pdf':
                import fitz
                doc = fitz.open(file_path)
                toc = doc.get_toc()
                if toc:
                    text = "TABLE OF CONTENTS:\n"
                    for item in toc:
                        text += f"{'  ' * (item[0]-1)}- {item[1]}\n"
                
                if len(text) < 500:
                    text += "\nINITIAL PAGES:\n"
                    for i in range(min(5, len(doc))):
                        text += doc[i].get_text() + "\n"
                        if len(text) > limit: break
                doc.close()
            elif ext == 'epub':
                import zipfile
                from bs4 import BeautifulSoup
                with zipfile.ZipFile(file_path) as z:
                    toc_file = None
                    for name in z.namelist():
                        if name.endswith('toc.ncx') or name.endswith('nav.xhtml'):
                            toc_file = name
                            break
                    if toc_file:
                        soup = BeautifulSoup(z.read(toc_file), 'xml' if toc_file.endswith('.ncx') else 'html.parser')
                        text = "TABLE OF CONTENTS:\n" + soup.get_text(separator='\n')
                    
                    if len(text) < 500:
                        text += "\nINITIAL PAGES:\n"
                        html_files = [f for f in z.namelist() if f.endswith('.html') or f.endswith('.xhtml')]
                        for html_file in html_files[:3]:
                            soup = BeautifulSoup(z.read(html_file), 'html.parser')
                            text += soup.get_text(separator='\n') + "\n"
                            if len(text) > limit: break
        except Exception as e:
            pass
        return text[:limit]

    def _handle_ai_btn_click(self):
        self.btn_ai.configure(state="disabled", text="⏳ Đang phân loại AI...")
        threading.Thread(target=self._ai_worker, daemon=True).start()
            
    def _reset_ai_btn(self):
        self.btn_ai.configure(state="disabled", text="✔️ Hoàn tất Phân loại", fg_color=Colors.SUCCESS)

    def _ai_worker(self):
        try:
            if not self.ai_classifier.cloud_client.is_ready:
                self._safe_ai_log("[LỖI] Vertex AI chưa được cấu hình. Vui lòng cấu hình trong Cài đặt.")
                return

            self._safe_ai_log(f"Bắt đầu xử lý {len(self.clean_files)} sách bằng Vertex AI + Rule Engine...")
            overrides = load_overrides()

            for i, f in enumerate(self.clean_files):
                if self._cancel_scan:
                    self._safe_ai_log("\n[!] Đã dừng luồng AI bởi người dùng.")
                    break

                self._safe_ai_log(f"\n[{i+1}] Fast Sampling: {f['name']}...")
                text_sample = self._get_sample_text(f['path'], f['ext'])
                if not text_sample.strip():
                    self._safe_ai_log("  -> [THÔNG BÁO] Không có nội dung text (định dạng không hỗ trợ), AI sẽ phân tích hoàn toàn dựa vào Tên file gốc.")

                if self._cancel_scan: break

                meta = self.ai_classifier.analyze_book(text_sample, f['name'])

                extracted_title = (meta.get('title') or '').strip() or Path(f['path']).stem
                author = (meta.get('author') or '').strip()

                if author and author.lower() != 'không rõ':
                    full_name = f"{extracted_title} - {author}"
                else:
                    full_name = extracted_title

                safe_title = "".join(c for c in full_name if c.isalnum() or c in (' ', '-', '_', '.', ',')).rstrip()
                if not safe_title: safe_title = Path(f['path']).stem

                cat_folder = classify_file(safe_title, overrides)
                self._safe_ai_log(f"  -> Title AI: {safe_title}")
                self._safe_ai_log(f"  -> Keyword Match Category: {cat_folder}")

                target_file_name = f"{safe_title}.{f['ext']}"
                source_path = Path(f['path']).resolve()
                duplicate_path = None

                # Check for exact name match across the entire library
                for existing in self.lib_dir.rglob(target_file_name):
                    if existing.resolve() != source_path:
                        duplicate_path = existing
                        break

                if duplicate_path is not None:
                    self._safe_ai_log(f"  -> [BỎ QUA] Đã tồn tại vật lý trên đĩa! Đang dọn dẹp...")
                    try:
                        clean_path = str(f['path']).replace('/', '\\')
                        if clean_path.startswith('\\\\?\\'):
                            clean_path = clean_path[4:]
                        try:
                            send2trash(clean_path)
                        except Exception as trash_error:
                            self._safe_ai_log(
                                f"  -> [LỖI] Không thể chuyển vào Thùng rác; "
                                f"file được giữ nguyên: {Path(f['path']).name} "
                                f"({trash_error})"
                            )
                            continue
                        self._safe_ai_log(f"  -> [XÓA] Đã dọn dẹp file tàn dư.")
                    except Exception as e:
                        self._safe_ai_log(f"  -> [LỖI] Xóa file: {e}")
                    continue
                
                if cat_folder == "_NOT_BIOLOGY":
                    target_dir = self.lib_dir / "_Review_Not_Biology"
                elif cat_folder == "_UNCLASSIFIED":
                    target_dir = self.lib_dir / "_UNCLASSIFIED"
                elif cat_folder == "_SKIP":
                    target_dir = self.lib_dir / "_SKIP"
                else:
                    target_dir = self.lib_dir / "Biology" / cat_folder
                    
                target_dir.mkdir(parents=True, exist_ok=True)
                dest_path = target_dir / f"{safe_title}.{f['ext']}"
                if dest_path.resolve() != source_path:
                    counter = 1
                    while dest_path.exists():
                        dest_path = target_dir / f"{safe_title}_{counter}.{f['ext']}"
                        counter += 1

                    try:
                        shutil.move(str(f['path']), str(dest_path))
                    except Exception as e:
                        self._safe_ai_log(f"  -> [LỖI] Di chuyển file: {e}")
                        continue
                else:
                    dest_path = source_path
                
                self._safe_ai_log(f"  -> Đã di chuyển: {dest_path.absolute()}")
                
                try:
                    book_id = self.db_manager.save_book_batch(
                        book_title=meta.get('title', safe_title),
                        author=meta.get('author', 'Không rõ'),
                        source_path=str(dest_path.absolute()),
                        cover_path='',
                        structured_content=[], 
                        published_year=str(meta.get('year', '')),
                        category=cat_folder
                    )
                    self._safe_ai_log(f"  -> Fast Ingest OK! (ID: {book_id})")
                except Exception as e:
                    self._safe_ai_log(f"  -> [LỖI] Lưu Database: {e}")
                
            self._safe_ai_log("\nHoàn tất xử lý AI!")
        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            self._safe_ai_log(f"\n[CRITICAL LỖI LUỒNG AI] Đã xảy ra lỗi nghiêm trọng:\n{err_msg}")
            print(f"Lỗi Thread _ai_worker: {e}")
        finally:
            self.after(0, self._reset_ai_btn)
            self.after(500, self._load_dashboard_data)

