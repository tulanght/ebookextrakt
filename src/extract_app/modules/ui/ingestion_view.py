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

PREDEFINED_CATEGORIES = [
    {"id": "Dong_Vat", "name": "Kho Động vật", "desc": "Sách động vật, thú y"},
    {"id": "Thuc_Vat", "name": "Kho Thực vật", "desc": "Nông nghiệp, thực vật"},
    {"id": "Dong_Vat_Va_Thuc_Vat", "name": "Động Thực vật (Overlap)", "desc": "Sinh học tổng hợp"},
    {"id": "Khac", "name": "Các chủ đề Khác", "desc": "Chờ phân loại mở rộng"}
]
MAIN_CATS = ["Dong_Vat", "Thuc_Vat", "Dong_Vat_Va_Thuc_Vat"]

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
        
        # Init predefined physical folders
        self.lib_dir = get_user_data_dir() / "library"
        for cat in PREDEFINED_CATEGORIES:
            (self.lib_dir / cat['id']).mkdir(parents=True, exist_ok=True)
            
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

    def _load_dashboard_data(self):
        for widget in self.dashboard_frame.winfo_children():
            widget.destroy()
            
        self.dashboard_frame.grid_columnconfigure((0, 1), weight=1)
            
        all_books = self.db_manager.get_all_books()
        db_path_map = {Path(b['source_path']).resolve(): b for b in all_books if b.get('source_path')}
        
        row_idx = 0
        col_idx = 0
        for cat in PREDEFINED_CATEGORIES:
            cat_path = self.lib_dir / cat['id']
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
            if is_dirty and current_cat_id in MAIN_CATS:
                btn_clean = ctk.CTkButton(actions_frame, text="✨ Chuẩn hóa AI", width=100, height=24, fg_color=Colors.SUCCESS,
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
        for cat in PREDEFINED_CATEGORIES:
            menu.add_command(label=f"Chuyển sang: {cat['name']}", command=lambda cid=cat['id'], p=file_path, b=db_info, rw=row_widget: self._move_file_and_ingest(cid, p, b, rw))
        
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        menu.tk_popup(x, y)
        
    def _move_file_and_ingest(self, target_cat_id: str, file_path: Path, db_info, row_widget):
        if target_cat_id == "Khac":
            target_dir = self.lib_dir / target_cat_id
            target_path = target_dir / file_path.name
            counter = 1
            while target_path.exists() and target_path.resolve() != file_path.resolve():
                target_path = target_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                counter += 1
            shutil.move(str(file_path), str(target_path))
            if db_info:
                conn = self.db_manager._get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM books WHERE id = ?", (db_info['id'],))
                conn.commit()
            self.after(500, self._load_dashboard_data)
        else:
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
            
            meta = self.ai_classifier.analyze_book(text_sample)
            extracted_title = meta.get('title', '').strip()
            if not extracted_title:
                extracted_title = file_path.stem
                
            safe_title = "".join(c for c in extracted_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not safe_title: safe_title = file_path.stem
            
            global_log(f"[MANUAL INGEST] Bắt đầu di chuyển: {file_path.name} -> {safe_title}")
            
            target_dir = self.lib_dir / target_cat_id
            target_path = target_dir / f"{safe_title}{file_path.suffix}"
            counter = 1
            while target_path.exists() and target_path.resolve() != file_path.resolve():
                target_path = target_dir / f"{safe_title}_{counter}{file_path.suffix}"
                counter += 1
                
            shutil.move(str(file_path), str(target_path))
            
            if db_info:
                conn = self.db_manager._get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE books SET title = ?, author = ?, published_year = ?, source_path = ? WHERE id = ?", 
                               (meta.get('title', safe_title), meta.get('author', ''), str(meta.get('year', '')), str(target_path.absolute()), db_info['id']))
                conn.commit()
            else:
                # BYPASS DEEP PARSING FOR INGESTION SPEED
                self.db_manager.save_book_batch(
                    book_title=meta.get('title', safe_title),
                    author=meta.get('author', 'Không rõ'),
                    source_path=str(target_path.absolute()),
                    cover_path='', # Cover and deep text parsing deferred to Phase 2 (Electron Reader)
                    structured_content=[], 
                    published_year=str(meta.get('year', ''))
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

    def _clean_single_worker(self, file_path: Path, db_info):
        try:
            ext = file_path.suffix.lower().replace('.', '')
            text_sample = self._get_sample_text(str(file_path), ext)
            meta = self.ai_classifier.analyze_book(text_sample)
            
            extracted_title = meta.get('title', '').strip()
            if not extracted_title:
                extracted_title = file_path.stem
                
            safe_title = "".join(c for c in extracted_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not safe_title: safe_title = file_path.stem
            
            global_log(f"[RENAME LOG] File gốc: {file_path.name} -> Tên mới: {safe_title}{file_path.suffix}")
            
            target_path = file_path.parent / f"{safe_title}{file_path.suffix}"
            counter = 1
            while target_path.exists() and target_path.resolve() != file_path.resolve():
                target_path = file_path.parent / f"{safe_title}_{counter}{file_path.suffix}"
                counter += 1
                
            shutil.move(str(file_path), str(target_path))
            
            if db_info:
                conn = self.db_manager._get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE books SET title = ?, author = ?, published_year = ?, source_path = ? WHERE id = ?", 
                               (meta.get('title', safe_title), meta.get('author', ''), str(meta.get('year', '')), str(target_path.absolute()), db_info['id']))
                conn.commit()
            else:
                # Just in case it's not in DB yet (e.g. batch clean)
                self.db_manager.save_book_batch(
                    book_title=meta.get('title', safe_title),
                    author=meta.get('author', 'Không rõ'),
                    source_path=str(target_path.absolute()),
                    cover_path='',
                    structured_content=[], 
                    published_year=str(meta.get('year', ''))
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
        
        for cat_id in MAIN_CATS:
            cat_path = self.lib_dir / cat_id
            if not cat_path.exists(): continue
            for f in cat_path.iterdir():
                if f.is_file() and f.suffix.lower() in ['.pdf', '.epub']:
                    is_dirty = ('z-lib' in f.name.lower() or '1lib' in f.name.lower() or '_1' in f.name.lower())
                    if is_dirty:
                        self._clean_single_worker(f.resolve(), db_path_map.get(f.resolve()))
                        
        self.after(0, lambda: self.btn_batch_clean.configure(state="normal", text="🧹 Dọn dẹp File Rác"))
        self.after(0, self._load_dashboard_data)

    def _remove_and_quarantine(self, book_id, file_path: Path, row_widget):
        try:
            conn = self.db_manager._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
            
            quar_dir = get_user_data_dir() / "quarantine"
            quar_dir.mkdir(parents=True, exist_ok=True)
            dest = quar_dir / file_path.name
            counter = 1
            while dest.exists():
                dest = quar_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                counter += 1
            shutil.move(str(file_path), str(dest))
            row_widget.destroy()
            self.after(500, self._load_dashboard_data)
        except Exception as e:
            print(f"Lỗi khi Gỡ bỏ: {e}")

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
                    
            for cat in PREDEFINED_CATEGORIES:
                cat_path = self.lib_dir / cat['id']
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
                    if ext in ['pdf', 'epub']:
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
        
        if db_dupes > 0:
            db_frame = ctk.CTkFrame(self.ingestion_frame, fg_color=Colors.BG_APP, border_width=1, border_color=Colors.WARNING)
            db_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
            ctk.CTkLabel(db_frame, text=f"📚 Trùng lặp với Thư viện Database ({db_dupes} files)", font=Fonts.BODY_BOLD, text_color=Colors.WARNING).pack(anchor="w", padx=Spacing.MD, pady=(Spacing.SM, 0))
            for i, f in enumerate(self.db_duplicates):
                f_frame = ctk.CTkFrame(db_frame, fg_color="transparent")
                f_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.XS)
                ctk.CTkLabel(f_frame, text=f"{f['name']}", font=Fonts.BODY).pack(side="left")
                ctk.CTkButton(f_frame, text="🔒 Cô lập", width=60, fg_color=Colors.WARNING, height=24, command=lambda path=f['path'], row_w=f_frame: self._quarantine_file(path, row_w)).pack(side="right", padx=Spacing.SM)
                
        for size, files in self.duplicate_groups.items():
            group_frame = ctk.CTkFrame(self.ingestion_frame, fg_color=Colors.BG_APP, border_width=1, border_color=Colors.DANGER)
            group_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)
            size_mb = round(size / (1024*1024), 2)
            ctk.CTkLabel(group_frame, text=f"⚠️ Trùng lặp nội bộ thư mục ({size_mb} MB)", font=Fonts.BODY_BOLD, text_color=Colors.DANGER).pack(anchor="w", padx=Spacing.MD, pady=(Spacing.SM, 0))
            for i, f in enumerate(files):
                f_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
                f_frame.pack(fill="x", padx=Spacing.MD, pady=Spacing.XS)
                ctk.CTkLabel(f_frame, text=f"{f['name']}", font=Fonts.BODY).pack(side="left")
                ctk.CTkButton(f_frame, text="🔒 Cô lập", width=60, fg_color=Colors.DANGER, height=24, command=lambda path=f['path'], row_w=f_frame: self._quarantine_file(path, row_w)).pack(side="right", padx=Spacing.SM)
                
        self._render_ai_step()
        
    def _quarantine_file(self, file_path, widget):
        try:
            quar_dir = get_user_data_dir() / "quarantine"
            quar_dir.mkdir(parents=True, exist_ok=True)
            p = Path(file_path)
            dest = quar_dir / p.name
            counter = 1
            while dest.exists():
                dest = quar_dir / f"{p.stem}_{counter}{p.suffix}"
                counter += 1
            shutil.move(str(p), str(dest))
            widget.destroy()
            self._insert_log(f"[CÔ LẬP] Đã di chuyển: {p.name} -> quarantine/")
        except Exception as e:
            self._insert_log(f"[LỖI CÔ LẬP] {e}")

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
        if self.btn_ai.cget("text") == "🛑 Dừng AI Lại":
            self._cancel_scan = True
            self.btn_ai.configure(state="disabled", text="Đang dừng...")
        else:
            self._cancel_scan = False
            self.btn_ai.configure(text="🛑 Dừng AI Lại", fg_color=Colors.DANGER, hover_color=Colors.DANGER_HOVER)
            threading.Thread(target=self._ai_worker, daemon=True).start()
            
    def _reset_ai_btn(self):
        self.btn_ai.configure(command=self._handle_ai_btn_click)
        self.btn_ai.configure(state="normal", text="✨ Bắt đầu Phân loại (Vertex AI)", fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER)

    def _ai_worker(self):
        if not self.ai_classifier.cloud_client.is_ready:
            self._safe_ai_log("[LỖI] Vertex AI chưa được cấu hình. Vui lòng cấu hình trong Cài đặt.")
            self.after(0, self._reset_ai_btn)
            return
            
        self._safe_ai_log(f"Bắt đầu xử lý {len(self.clean_files)} sách bằng Vertex AI...")
        
        all_books = self.db_manager.get_all_books()
        db_titles = {b['title'].lower().strip() for b in all_books if b.get('title')}
        
        for i, f in enumerate(self.clean_files):
            if self._cancel_scan:
                self._safe_ai_log("\n[!] Đã dừng luồng AI bởi người dùng.")
                break
                
            self._safe_ai_log(f"\n[{i+1}] Fast Sampling file: {f['name']}...")
            
            # --- 1. FAST SAMPLING ---
            text_sample = self._get_sample_text(f['path'], f['ext'])
            if not text_sample.strip():
                self._safe_ai_log("  -> [BỎ QUA] Không trích xuất được text.")
                continue
                
            if self._cancel_scan: break
            
            # --- 2. AI CLASSIFICATION & METADATA ---
            meta = self.ai_classifier.analyze_book(text_sample)
            cat_id = meta.get("category_id", "Khac")
            self._safe_ai_log(f"  -> Thể loại: {cat_id} ({meta.get('reason', '')})")
            
            if self._cancel_scan: break
            
            # --- FIREWALL: BỎ QUA CHUẨN HÓA NẾU LÀ KHO 'Khac' ---
            if cat_id == "Khac":
                self._safe_ai_log("  -> [BỎ QUA METADATA] Sách vào kho Khác, giữ nguyên tên gốc.")
            else:
                self._safe_ai_log(f"  -> Metadata: {meta}")
            
            extracted_title = meta.get('title', '').strip()
            if extracted_title and extracted_title.lower() in db_titles:
                self._safe_ai_log(f"  -> [BỎ QUA] Sách '{extracted_title}' đã tồn tại trong Database!")
                continue
            
            # --- 4. DI CHUYỂN FILE VẬT LÝ ---
            lib_dir = self.lib_dir / cat_id
            lib_dir.mkdir(parents=True, exist_ok=True)
            
            # Nếu là Khác, giữ nguyên tên gốc. Nếu là Sinh Học, lấy tên chuẩn.
            safe_title = "".join(c for c in meta.get('title', f['name']) if c.isalnum() or c in (' ', '-', '_')).rstrip() if cat_id != "Khac" else f['name']
            if not safe_title: safe_title = "Unknown_Book"
            dest_filename = f"{safe_title}.{f['ext']}" if cat_id != "Khac" else safe_title
            dest_path = lib_dir / dest_filename
            
            counter = 1
            while dest_path.exists():
                if cat_id != "Khac":
                    dest_path = lib_dir / f"{safe_title}_{counter}.{f['ext']}"
                else:
                    dest_path = lib_dir / f"{Path(safe_title).stem}_{counter}{Path(safe_title).suffix}"
                counter += 1
                
            self._safe_ai_log(f"  -> [Bước 5] Di chuyển sách vào kho: {dest_path.absolute()}")
            try:
                shutil.copy2(f['path'], dest_path)
            except Exception as e:
                self._safe_ai_log(f"  -> [LỖI] Lỗi copy file: {e}")
                continue
            
            if self._cancel_scan: break
            
            # --- 5. FAST INGEST (BYPASS DEEP PARSING) ---
            if cat_id != "Khac":
                self._safe_ai_log(f"  -> [Bước 6] Fast Ingest: Lưu Database (Bỏ qua Deep Parse)...")
                try:
                    book_id = self.db_manager.save_book_batch(
                        book_title=meta.get('title', safe_title),
                        author=meta.get('author', 'Không rõ'),
                        source_path=str(dest_path.absolute()),
                        cover_path='', # Cover and content deep parse deferred to Reader View
                        structured_content=[], 
                        published_year=str(meta.get('year', ''))
                    )
                    self._safe_ai_log(f"  -> Hoàn tất Fast Ingest! (Book ID: {book_id})")
                except Exception as e:
                    self._safe_ai_log(f"  -> [LỖI] Lưu Database: {e}")
            else:
                self._safe_ai_log(f"  -> [Bước 6] Bỏ qua Ingest vì là kho Khác.")
            
        self._safe_ai_log("\nHoàn tất quá trình xử lý AI!")
        self.after(0, self._reset_ai_btn)
        self.after(500, self._load_dashboard_data)

