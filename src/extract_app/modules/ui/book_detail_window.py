# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/book_detail_window.py
# Version: 1.0.0
# Author: Antigravity
# Description: BookDetailWindow — popup showing chapters, articles, queue controls,
#              export options and AI glossary extraction for a single book.
#              Extracted from library_view.py (Phase 3B refactor).
# --------------------------------------------------------------------------------

import tkinter as tk
import tkinter.filedialog as fd
import threading
import time
from pathlib import Path
from typing import Dict, List
import customtkinter as ctk
import shutil
import webbrowser

from .theme import Colors, Fonts, Spacing
from .custom_dialog import ask_yes_no, show_info, show_warning, show_error
from .tooltip import ToolTip
from .editor_view import DualViewEditor
from ...core import webview_generator
from ...core.eta_calculator import calculate_book_eta, update_dynamic_wpm
from ...core.queue_manager import ChapterQueueManager, ChapterQueueItem, QueueStatus
from ...core.config import get_user_data_dir


class BookDetailWindow(ctk.CTkToplevel):
    """
    Popup window showing book chapters and articles (Dark Navy theme).
    Provides:
      - Chapter/article list with translation status
      - Per-article translation & queue controls
      - Variant transforms (Website / Facebook)
      - Checkbox-based multi-select + export (Markdown / TXT / 只译文)
      - AI glossary extraction modal
      - Webview preview
    """

    def __init__(self, master, book_details: Dict, translation_service, db_manager, settings_manager):
        super().__init__(master, fg_color=Colors.BG_APP)
        self.title(book_details.get('title', 'Chi tiết sách'))
        self.geometry("900x700")

        self.translation_service = translation_service
        self.db_manager = db_manager
        self.settings_manager = settings_manager

        # Data
        self.book_id = book_details.get('id')
        self.chapters = book_details.get('chapters', [])

        # Checkbox state: article_id -> tk.BooleanVar
        self.article_checks: Dict[int, tk.BooleanVar] = {}

        # Chapter Queue Manager (one per open book window)
        self.queue_manager = ChapterQueueManager(
            translation_service=translation_service,
            db_manager=db_manager,
            settings_manager=settings_manager,
            on_item_done=lambda art_id, ok: self.after(0, lambda: self._on_queue_item_done(art_id, ok)),
            on_queue_done=lambda: self.after(0, self._on_queue_done),
            on_status_change=lambda s: self.after(0, lambda: self._on_queue_status_change(s)),
        )

        # ── Header ────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text=book_details.get('title', ''),
            font=Fonts.H2, text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(Spacing.XL, Spacing.SM))

        ctk.CTkLabel(
            self, text=book_details.get('author', ''),
            font=Fonts.BODY, text_color=Colors.TEXT_MUTED
        ).pack(pady=(0, Spacing.XL))

        # ── Tools Bar ─────────────────────────────────────────────────
        self.tools_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tools_frame.pack(fill="x", padx=Spacing.XL, pady=(0, Spacing.MD))

        self.btn_webview = ctk.CTkButton(
            self.tools_frame, text="📖 Đọc Thử (Webview)",
            font=Fonts.BODY_BOLD, fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY,
            hover_color=Colors.PRIMARY_HOVER, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._generate_and_open_webview
        )
        self.btn_webview.pack(side="left")

        self.btn_ai_glossary = ctk.CTkButton(
            self.tools_frame, text="🪄 AI Tạo Từ Vựng",
            font=Fonts.BODY_BOLD, fg_color="transparent", border_width=1, border_color=Colors.WARNING,
            text_color=Colors.WARNING, hover_color=Colors.BG_CARD_HOVER, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._open_ai_glossary_modal
        )
        self.btn_ai_glossary.pack(side="left", padx=Spacing.MD)

        # ETA label
        engine = settings_manager.get("translation_engine", "cloud")
        wpm_key = f"{engine}_llm_wpm"
        default_wpm = 6000 if engine == "cloud" else 180
        wpm = int(settings_manager.get(wpm_key, default_wpm))
        eta_text = calculate_book_eta(book_details.get('chapters', []), wpm=wpm, engine=engine)
        self.lbl_eta = ctk.CTkLabel(
            self.tools_frame, text=f"⏱ Ước tính dịch: {eta_text}",
            font=Fonts.SMALL, text_color=Colors.TEXT_MUTED
        )
        self.lbl_eta.pack(side="right", padx=Spacing.MD)

        # ── Queue Control Bar ─────────────────────────────────────────
        self.queue_bar = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=8)
        self.queue_bar.pack(fill="x", padx=Spacing.XL, pady=(0, Spacing.SM))

        self.lbl_queue_status = ctk.CTkLabel(
            self.queue_bar, text="📋 Hàng đợi: Chưa có bài nào",
            font=Fonts.SMALL, text_color=Colors.TEXT_MUTED
        )
        self.lbl_queue_status.pack(side="left", padx=Spacing.MD, pady=Spacing.SM)

        self.btn_queue_stop = ctk.CTkButton(
            self.queue_bar, text="⏹ Dừng", width=70, height=26,
            fg_color="transparent", border_width=1, border_color=Colors.DANGER,
            text_color=Colors.DANGER, hover_color=Colors.BG_CARD_HOVER,
            font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._stop_queue
        )
        self.btn_queue_stop.pack(side="right", padx=2, pady=Spacing.SM)

        self.btn_queue_pause = ctk.CTkButton(
            self.queue_bar, text="⏸ Tạm dừng", width=90, height=26,
            fg_color="transparent", border_width=1, border_color=Colors.WARNING,
            text_color=Colors.WARNING, hover_color=Colors.BG_CARD_HOVER,
            font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._toggle_pause_queue
        )
        self.btn_queue_pause.pack(side="right", padx=2, pady=Spacing.SM)

        self.btn_queue_start = ctk.CTkButton(
            self.queue_bar, text="▶ Bắt đầu Queue", width=120, height=26,
            fg_color=Colors.SUCCESS, text_color="white",
            hover_color="#1a8a4a",
            font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
            command=self._start_queue
        )
        self.btn_queue_start.pack(side="right", padx=(2, Spacing.MD), pady=Spacing.SM)

        # ── Article List ──────────────────────────────────────────────
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=Colors.BG_CARD, corner_radius=Spacing.CARD_RADIUS,
            scrollbar_button_color=Colors.BORDER, scrollbar_button_hover_color=Colors.TEXT_MUTED
        )
        self.list_frame.pack(fill="both", expand=True, padx=Spacing.XL, pady=(Spacing.XL, 0))

        # ── Export Bottom Bar ─────────────────────────────────────────
        export_bar = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=8)
        export_bar.pack(fill="x", padx=Spacing.XL, pady=(Spacing.SM, Spacing.MD))

        self.select_all_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            export_bar, text="Chọn tất cả", variable=self.select_all_var,
            command=self._toggle_select_all,
            fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.SMALL, width=120
        ).pack(side="left", padx=Spacing.MD, pady=Spacing.SM)

        self.export_format_var = tk.StringVar(value="Markdown")
        ctk.CTkOptionMenu(
            export_bar, variable=self.export_format_var,
            values=["Markdown", "TXT", "Chỉ bản dịch"],
            width=130,
            fg_color=Colors.BG_INPUT, button_color=Colors.BORDER,
            button_hover_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY,
            dropdown_fg_color=Colors.BG_CARD, dropdown_text_color=Colors.TEXT_PRIMARY,
            font=Fonts.SMALL
        ).pack(side="left", padx=(0, Spacing.SM), pady=Spacing.SM)

        ctk.CTkButton(
            export_bar, text="📤 Xuất đã chọn",
            font=Fonts.BODY_BOLD, fg_color=Colors.SUCCESS, text_color=Colors.TEXT_PRIMARY,
            hover_color=Colors.SUCCESS_HOVER, corner_radius=Spacing.BUTTON_RADIUS,
            width=140, command=self._export_selected
        ).pack(side="right", padx=Spacing.MD, pady=Spacing.SM)

        self.lbl_export_status = ctk.CTkLabel(
            export_bar, text="", font=Fonts.SMALL, text_color=Colors.TEXT_MUTED
        )
        self.lbl_export_status.pack(side="right", padx=Spacing.SM)

        self._render_content()

        # Ensure window appears on top (Windows fix)
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        self.focus_force()

    # ─────────────────────────────────────────────────────────────────
    # Content Rendering
    # ─────────────────────────────────────────────────────────────────

    def _render_content(self):
        """Refresh chapter/article list from DB."""
        if self.book_id:
            fresh_data = self.db_manager.get_book_details(self.book_id)
            if fresh_data:
                self.chapters = fresh_data.get('chapters', [])

        if not self.winfo_exists() or not self.list_frame.winfo_exists():
            return

        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for chapter in self.chapters:
            all_articles = chapter.get('articles', [])

            total_words = sum(a.get('word_count', 0) or 0 for a in all_articles)
            total_translated = sum(1 for a in all_articles if a.get('status') == 'translated' and a.get('is_leaf', 1))
            total_leaf = sum(1 for a in all_articles if a.get('is_leaf', 1))

            # Chapter Header
            chap_frame = ctk.CTkFrame(self.list_frame, fg_color=Colors.BG_CARD_HOVER, corner_radius=Spacing.BUTTON_RADIUS)
            chap_frame.pack(fill="x", pady=(Spacing.MD, Spacing.XS), padx=0)

            ctk.CTkLabel(
                chap_frame, text=f"📂 {chapter.get('title', 'Unknown Chapter')}",
                font=Fonts.H3, text_color=Colors.TEXT_PRIMARY, anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=Spacing.MD, pady=Spacing.SM)

            progress_text = f"{total_translated}/{total_leaf}" if total_leaf > 0 else "0"
            ctk.CTkLabel(
                chap_frame, text=f"{total_words:,} từ | {progress_text} đã dịch",
                font=Fonts.TINY, text_color=Colors.TEXT_MUTED
            ).pack(side="right", padx=Spacing.MD, pady=Spacing.SM)

            parent_articles = [a for a in all_articles if not a.get('is_leaf', 1)]
            leaf_articles = [a for a in all_articles if a.get('is_leaf', 1)]

            if parent_articles and leaf_articles:
                for parent in parent_articles:
                    if (parent.get('word_count', 0) or 0) > 0:
                        self._render_article_row(parent, indent=Spacing.MD, is_parent=True)
                for article in leaf_articles:
                    self._render_article_row(article, indent=Spacing.XL + Spacing.MD)
            else:
                for article in all_articles:
                    self._render_article_row(article, indent=Spacing.MD)

    def _render_article_row(self, article, indent=0, is_parent=False):
        """Render a single article row with status dot, buttons and optional checkbox."""
        status = article.get('status', 'new')
        is_translated = status == 'translated'
        is_leaf = article.get('is_leaf', 1)
        article_id = article.get('id')

        if is_parent:
            art_frame = ctk.CTkFrame(self.list_frame, fg_color=Colors.BG_CARD, corner_radius=Spacing.BUTTON_RADIUS)
            art_frame.pack(fill="x", pady=(Spacing.SM, 1), padx=indent)

            word_count = article.get('word_count', 0) or 0
            ctk.CTkLabel(
                art_frame, text=f"  📄 {article.get('subtitle', '')}",
                font=Fonts.BODY_BOLD, text_color=Colors.TEXT_SECONDARY, anchor="w"
            ).pack(side="left", padx=Spacing.SM, fill="x", expand=True)

            right_frame = ctk.CTkFrame(art_frame, fg_color="transparent")
            right_frame.pack(side="right", fill="y", padx=Spacing.SM)

            ctk.CTkLabel(
                right_frame, text=f"{word_count:,} từ (giới thiệu)",
                text_color=Colors.TEXT_MUTED, font=Fonts.TINY
            ).pack(side="left", padx=(Spacing.SM, Spacing.MD))

            if is_translated:
                ctk.CTkButton(
                    right_frame, text="Biên tập", width=72, height=26,
                    fg_color="transparent", border_width=1, border_color=Colors.SUCCESS,
                    text_color=Colors.SUCCESS, hover_color=Colors.BG_CARD_HOVER,
                    font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                    command=lambda a=article: self._open_dual_view(a)
                ).pack(side="left", padx=2, pady=4)
            elif word_count > 50:
                ctk.CTkButton(
                    right_frame, text="📥 Dịch Lưu trữ", width=110, height=26,
                    fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY, hover_color=Colors.PRIMARY_HOVER,
                    font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                    command=lambda a=article: self._translate_article(a)
                ).pack(side="left", padx=2, pady=4)
            return

        # Leaf article row
        art_frame = ctk.CTkFrame(self.list_frame, fg_color=Colors.BG_APP, corner_radius=Spacing.BUTTON_RADIUS)
        art_frame.pack(fill="x", pady=2, padx=indent)

        status_color = Colors.SUCCESS if is_translated else Colors.TEXT_MUTED

        # Checkbox
        if article_id not in self.article_checks:
            self.article_checks[article_id] = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            art_frame, text="", variable=self.article_checks[article_id],
            fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_HOVER,
            width=20, height=20, checkbox_width=16, checkbox_height=16
        ).pack(side="left", padx=(Spacing.SM, 2))

        # Status dot
        canvas = ctk.CTkCanvas(art_frame, width=10, height=10, bg=Colors.BG_APP, highlightthickness=0)
        canvas.create_oval(2, 2, 8, 8, fill=status_color)
        canvas.pack(side="left", padx=(0, Spacing.SM))

        # Right side
        right_frame = ctk.CTkFrame(art_frame, fg_color="transparent")
        right_frame.pack(side="right", fill="y", padx=Spacing.SM)

        word_count = article.get('word_count', 0) or 0
        translated_at = article.get('translated_at')
        meta_str = f"{word_count:,} từ"
        if translated_at:
            meta_str += f" | {str(translated_at)[:10]}"
        ctk.CTkLabel(right_frame, text=meta_str, text_color=Colors.TEXT_MUTED, font=Fonts.TINY).pack(
            side="left", padx=(Spacing.SM, Spacing.MD)
        )

        ctk.CTkLabel(
            art_frame, text=article.get('subtitle', 'No Subtitle'),
            font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left", padx=Spacing.SM, fill="x", expand=True)

        if is_leaf:
            if is_translated:
                ctk.CTkButton(
                    right_frame, text="Biên tập", width=72, height=26,
                    fg_color="transparent", border_width=1, border_color=Colors.SUCCESS,
                    text_color=Colors.SUCCESS, hover_color=Colors.BG_CARD_HOVER,
                    font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                    command=lambda a=article: self._open_dual_view(a)
                ).pack(side="left", padx=2, pady=4)

                engine = self.settings_manager.get("translation_engine", "cloud")
                btn_state = "normal" if engine == "cloud" else "disabled"

                has_web = bool(article.get('website_text'))
                btn_web = ctk.CTkButton(
                    right_frame, text="🌐", width=32, height=26, state=btn_state,
                    fg_color=Colors.BG_CARD if has_web else "transparent",
                    border_width=1, border_color=Colors.PRIMARY,
                    text_color=Colors.PRIMARY, hover_color=Colors.BG_CARD_HOVER,
                    font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                    command=lambda a=article: self._transform_article(a, 'website')
                )
                btn_web.pack(side="left", padx=2, pady=4)
                ToolTip(btn_web, "Chuyển thành bài viết Website SEO")

                has_fb = bool(article.get('facebook_text'))
                btn_fb = ctk.CTkButton(
                    right_frame, text="📱", width=32, height=26, state=btn_state,
                    fg_color=Colors.BG_CARD if has_fb else "transparent",
                    border_width=1, border_color=Colors.WARNING,
                    text_color=Colors.WARNING, hover_color=Colors.BG_CARD_HOVER,
                    font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                    command=lambda a=article: self._transform_article(a, 'facebook')
                )
                btn_fb.pack(side="left", padx=2, pady=4)
                ToolTip(btn_fb, "Chuyển thành bài viết Facebook")

                ctk.CTkButton(
                    right_frame, text="🔄 Dịch Lại", width=80, height=26,
                    fg_color="transparent", border_width=1, border_color=Colors.WARNING,
                    text_color=Colors.WARNING, hover_color=Colors.BG_CARD_HOVER,
                    font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                    command=lambda a=article: self._translate_article(a, force_retranslate=True)
                ).pack(side="left", padx=2, pady=4)
            else:
                ctk.CTkButton(
                    right_frame, text="📥 Dịch Lưu trữ", width=110, height=26,
                    fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY, hover_color=Colors.PRIMARY_HOVER,
                    font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                    command=lambda a=article: self._translate_article(a)
                ).pack(side="left", padx=2, pady=4)

                is_queued = self.queue_manager.is_queued(article_id)
                q_text = "✖ Hủy Queue" if is_queued else "➕ Thêm Queue"
                q_color = Colors.DANGER if is_queued else Colors.TEXT_MUTED
                ctk.CTkButton(
                    right_frame, text=q_text, width=90, height=26,
                    fg_color="transparent", border_width=1, border_color=q_color,
                    text_color=q_color, hover_color=Colors.BG_CARD_HOVER,
                    font=Fonts.SMALL, corner_radius=Spacing.BUTTON_RADIUS,
                    command=lambda a=article: self._toggle_article_queue(a)
                ).pack(side="left", padx=2, pady=4)
        else:
            ctk.CTkLabel(right_frame, text="(Mục lục)", text_color=Colors.TEXT_MUTED, font=Fonts.TINY).pack(
                side="left", padx=Spacing.MD, pady=2
            )

    # ─────────────────────────────────────────────────────────────────
    # Export / Selection Methods
    # ─────────────────────────────────────────────────────────────────

    def _toggle_select_all(self):
        selected = self.select_all_var.get()
        for var in self.article_checks.values():
            var.set(selected)

    def _export_selected(self):
        """Export ticked articles to a file."""
        fmt = self.export_format_var.get()
        selected_ids = {art_id for art_id, var in self.article_checks.items() if var.get()}
        if not selected_ids:
            show_warning(self, "Chưa chọn bài", "Hãy tick chọn ít nhất 1 bài trước khi xuất!")
            return

        ext = ".md" if fmt == "Markdown" else ".txt"
        filetypes = [("Markdown", "*.md"), ("Tất cả", "*.*")] if fmt == "Markdown" else [("Text file", "*.txt"), ("Tất cả", "*.*")]
        save_path = fd.asksaveasfilename(parent=self, defaultextension=ext, filetypes=filetypes, initialfile=f"export{ext}")
        if not save_path:
            return

        lines = []
        for chapter in self.chapters:
            chapter_articles = [a for a in chapter.get('articles', []) if a.get('id') in selected_ids and a.get('is_leaf', 1)]
            if not chapter_articles:
                continue

            if fmt == "Markdown":
                lines.append(f"# {chapter.get('title', 'Chapter')}\n")
            elif fmt == "TXT":
                lines.append(f"=== {chapter.get('title', 'Chapter')} ===\n")

            for art in chapter_articles:
                subtitle = art.get('subtitle', '')
                content = self.db_manager.get_article_content(art['id']) or ''
                translation = art.get('translation_text', '') or ''

                if fmt == "Markdown":
                    lines.append(f"## {subtitle}\n")
                    if content:
                        lines.append(f"**Nội dung gốc:**\n\n{content}\n")
                    if translation:
                        lines.append(f"**Bản dịch:**\n\n{translation}\n")
                    lines.append("---\n")
                elif fmt == "TXT":
                    lines.append(f"[{subtitle}]\n")
                    if content:
                        lines.append(f"{content}\n")
                    if translation:
                        lines.append(f"--- Bản dịch ---\n{translation}\n")
                    lines.append("\n")
                elif fmt == "Chỉ bản dịch":
                    text = translation or content
                    if text:
                        lines.append(f"# {subtitle}\n\n{text}\n\n---\n")

        try:
            Path(save_path).write_text("\n".join(lines), encoding="utf-8")
            self.lbl_export_status.configure(text=f"✓ Đã xuất {len(selected_ids)} bài", text_color=Colors.SUCCESS)
            self.after(3000, lambda: self.lbl_export_status.configure(text=""))
        except Exception as e:
            show_error(self, "Lỗi xuất file", str(e))

    # ─────────────────────────────────────────────────────────────────
    # Queue Control Methods
    # ─────────────────────────────────────────────────────────────────

    def _toggle_article_queue(self, article: Dict) -> None:
        article_id = article.get('id')
        if self.queue_manager.is_queued(article_id):
            self.queue_manager.remove(article_id)
        else:
            content = self.db_manager.get_article_content(article_id) or ""
            if not content:
                show_warning(self, "Nội dung trống", "Bài viết này không có nội dung để dịch.")
                return
            self.queue_manager.enqueue(ChapterQueueItem(
                article_id=article_id,
                subtitle=article.get('subtitle', ''),
                word_count=article.get('word_count', 0) or 0,
                content=content,
            ))
        self._render_content()
        self._update_queue_status_label()

    def _start_queue(self) -> None:
        if not self.queue_manager.pending_ids:
            show_info(self, "Hàng đợi trống", "Hãy thêm ít nhất 1 bài vào hàng đợi trước bằng nút '➕ Thêm Queue'.")
            return
        self.queue_manager.start()

    def _toggle_pause_queue(self) -> None:
        if self.queue_manager.status == "paused":
            self.queue_manager.resume()
        else:
            self.queue_manager.pause()

    def _stop_queue(self) -> None:
        self.queue_manager.stop()
        self._render_content()
        self._update_queue_status_label()

    def _on_queue_item_done(self, article_id: int, success: bool) -> None:
        self._render_content()
        self._refresh_eta()
        self._update_queue_status_label()

    def _on_queue_done(self) -> None:
        self._update_queue_status_label()
        show_info(self, "✅ Hoàn tất", "Hàng đợi dịch đã xử lý xong tất cả các bài!")

    def _on_queue_status_change(self, status: str) -> None:
        if status == "paused":
            self.btn_queue_pause.configure(text="▶ Tiếp tục")
        else:
            self.btn_queue_pause.configure(text="⏸ Tạm dừng")
        self._update_queue_status_label()

    def _update_queue_status_label(self) -> None:
        if not self.winfo_exists() or not hasattr(self, 'lbl_queue_status'):
            return
        pending = len(self.queue_manager.pending_ids)
        done = getattr(self.queue_manager, 'done_count', 0)
        total = pending + done
        status = self.queue_manager.status

        if total == 0:
            text = "📋 Hàng đợi: Chưa có bài nào"
        elif status == "running":
            pct = int(done / total * 100) if total > 0 else 0
            text = f"🖥️ Đang dịch bài {done + 1}/{total}  ({pct}% hoàn thành)"
        elif status == "paused":
            pct = int(done / total * 100) if total > 0 else 0
            text = f"⏸ Tạm dừng ({pct}% — {pending} bài còn lại)"
        else:
            text = f"📋 Hàng đợi: {pending} bài chờ dịch"
        self.lbl_queue_status.configure(text=text)

    # ─────────────────────────────────────────────────────────────────
    # AI Glossary Extraction
    # ─────────────────────────────────────────────────────────────────

    def _open_ai_glossary_modal(self):
        if not self.translation_service.api_key:
            show_warning(self, "Thiếu API Key", "Vui lòng nhập Cloud API Key (Gemini) trong phần Cài đặt trước.")
            return

        categories = self.translation_service.glossary_manager.get_categories()

        modal = ctk.CTkToplevel(self)
        modal.title("🪄 Tự động trích xuất Từ Vựng bằng AI")
        modal.geometry("480x380")
        modal.transient(self)
        modal.grab_set()
        modal.config(bg=Colors.BG_APP)

        ctk.CTkLabel(
            modal, text="AI (Gemini) sẽ đọc một phần nội dung sách để tự động tìm và\ntạo danh sách 30-50 từ khóa/thuật ngữ quan trọng nhất.",
            font=Fonts.BODY, text_color=Colors.TEXT_MUTED, justify="left"
        ).pack(pady=(20, 10), padx=20, fill="x")

        form = ctk.CTkFrame(modal, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(form, text="Chủ đề sách (Để AI dịch chuẩn ngữ cảnh):", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", pady=5)
        entry_subject = ctk.CTkEntry(form, width=300, fg_color=Colors.BG_INPUT, border_color=Colors.BORDER)
        entry_subject.insert(0, self.title()[:30] + "...")
        entry_subject.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(form, text="Lưu vào danh mục từ vựng:", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).grid(row=2, column=0, sticky="w", pady=5)
        combo_category = ctk.CTkComboBox(
            form, width=300, values=categories if categories else ["Sách mới"],
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, button_color=Colors.PRIMARY
        )
        active = self.translation_service.glossary_manager.get_active_category()
        combo_category.set(active if active and active in categories else (categories[0] if categories else "Sách mới"))
        combo_category.grid(row=3, column=0, sticky="ew", pady=(0, 20))

        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        def on_start():
            subject = entry_subject.get().strip()
            target_cat = combo_category.get().strip()
            if not subject or not target_cat:
                show_warning(modal, "Thiếu thông tin", "Vui lòng điền đủ Chủ đề và Danh mục.")
                return
            modal.destroy()
            self._start_ai_glossary_extraction(subject, target_cat)

        ctk.CTkButton(btn_frame, text="Bắt đầu Trích xuất 🚀", width=140, height=32, fg_color=Colors.PRIMARY, text_color=Colors.TEXT_PRIMARY, command=on_start).pack(side="right")
        ctk.CTkButton(btn_frame, text="Hủy", width=80, height=32, fg_color="transparent", border_color=Colors.BORDER, border_width=1, text_color=Colors.TEXT_MUTED, command=modal.destroy).pack(side="right", padx=10)

    def _start_ai_glossary_extraction(self, subject: str, target_category: str):
        all_article_ids = [a['id'] for ch in self.chapters for a in ch.get('articles', []) if a.get('is_leaf', 1)]
        if not all_article_ids:
            show_warning(self, "Cảnh báo", "Sách này chưa có bài viết nào.")
            return

        total = len(all_article_ids)
        segment_size = max(1, total // 3)
        segments = [s for s in [all_article_ids[:segment_size], all_article_ids[segment_size:2*segment_size], all_article_ids[2*segment_size:]] if s]
        chars_per_segment = 15000 // len(segments)
        sample_text = ""
        for segment in segments:
            seg_text = ""
            for art_id in segment:
                content = self.db_manager.get_article_content(art_id)
                if content:
                    seg_text += content + "\n\n"
                if len(seg_text) > chars_per_segment:
                    break
            sample_text += seg_text

        if len(sample_text) < 500:
            show_warning(self, "Cảnh báo", "Sách này quá ngắn hoặc chưa có chữ để trích xuất.")
            return

        self.loading_win = ctk.CTkToplevel(self)
        self.loading_win.title("🪄 AI đang tạo Từ Vựng...")
        self.loading_win.geometry("380x130")
        self.loading_win.transient(self)
        self.loading_win.grab_set()
        ctk.CTkLabel(self.loading_win, text=f"Lấy mẫu từ {len(segments)} phần sách ({len(sample_text[:15000]):,} ký tự)...", font=("Segoe UI", 12)).pack(pady=(20, 5))
        self.progress_bar = ctk.CTkProgressBar(self.loading_win, mode="indeterminate", width=250)
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()

        def worker():
            terms, err = self.translation_service.extract_glossary_from_text(sample_text, subject)
            self.after(0, lambda: self._on_glossary_extraction_complete(terms, err, target_category))

        threading.Thread(target=worker, daemon=True).start()

    def _on_glossary_extraction_complete(self, terms: list, error: str, target_category: str):
        if hasattr(self, 'loading_win') and self.loading_win.winfo_exists():
            self.loading_win.destroy()
        if error or not terms:
            show_error(self, "Lỗi Trích xuất", error or "Không có từ vựng nào được trích xuất.")
            return

        gm = self.translation_service.glossary_manager
        if target_category not in gm.get_categories():
            gm.add_category(target_category)
        terms_dict = {t.get('en', '').strip(): t.get('vi', '').strip() for t in terms if t.get('en') and t.get('vi')}
        added_count = gm.bulk_add_terms(terms_dict, target_category)
        show_info(self, "Hoàn tất 🪄", f"Đã phân tích xong!\n\nLưu thành công {added_count}/{len(terms)} từ vựng vào danh mục '{target_category}'.\n(Các từ trùng/lỗi cấu trúc bị bỏ qua).\n\n💡 Vào Cài đặt → Từ Vựng để xem và tinh chỉnh lại.")

    # ─────────────────────────────────────────────────────────────────
    # Translation Workflow
    # ─────────────────────────────────────────────────────────────────

    def _translate_article(self, article, force_retranslate=False):
        engine = self.settings_manager.get("translation_engine", "cloud")
        if engine == "cloud" and not self.translation_service.api_key:
            show_warning(self, "Thiếu API Key", "Vui lòng nhập API Key trong phần Cài đặt trước.")
            return

        if force_retranslate:
            if not ask_yes_no(self, "Xác nhận", "Bài viết này đã có bản dịch. Bạn có chắc muốn DỊCH LẠI (bản cũ sẽ bị ghi đè)?", is_danger=True):
                return
        else:
            if not ask_yes_no(self, "Xác nhận", f"Bắt đầu dịch bài viết này bằng {engine.upper()} API?"):
                return

        article_id = article['id']
        content_text = self.db_manager.get_article_content(article_id)
        if not content_text:
            show_warning(self, "Lỗi", "Không tìm thấy nội dung bài viết trong cơ sở dữ liệu.")
            return

        self._translation_start_time = time.time()
        self.loading_win = ctk.CTkToplevel(self)
        self.loading_win.title("Đang dịch...")
        self.loading_win.geometry("420x200")
        self.loading_win.transient(self)
        self.loading_win.grab_set()
        self.loading_win.resizable(False, False)

        ctk.CTkLabel(self.loading_win, text=f"📝 {article.get('subtitle', 'bài viết')[:40]}", font=("Segoe UI", 13, "bold"), text_color="#e0e0e0").pack(pady=(15, 2))
        self.timer_label = ctk.CTkLabel(self.loading_win, text="00:00", font=("Consolas", 32, "bold"), text_color="#4fc3f7")
        self.timer_label.pack(pady=(5, 5))
        self.progress_label = ctk.CTkLabel(self.loading_win, text="Chuẩn bị...", font=("Segoe UI", 11), text_color="gray")
        self.progress_label.pack(pady=(0, 5))
        self.progress_bar = ctk.CTkProgressBar(self.loading_win, mode="indeterminate", height=12, corner_radius=6, progress_color="#4fc3f7")
        self.progress_bar.pack(pady=(0, 15), padx=30, fill="x")
        self.progress_bar.start()
        _switched = [False]
        self._tick_translation_timer()

        def progress_callback(current, total, status):
            def update():
                if hasattr(self, 'loading_win') and self.loading_win.winfo_exists():
                    if total > 1 and not _switched[0]:
                        self.progress_bar.stop()
                        self.progress_bar.configure(mode="determinate")
                        _switched[0] = True
                    if total > 1:
                        pct = current / total
                        self.progress_bar.set(pct)
                        self.progress_label.configure(text=f"{status}  ({int(pct*100)}%)")
                    else:
                        self.progress_label.configure(text=status)
            self.after(0, update)

        def worker():
            try:
                chunk_size = self.settings_manager.get("chunk_size", 3000)
                chunk_delay = self.settings_manager.get("chunk_delay", 2.0)
                engine = self.settings_manager.get("translation_engine", "cloud")
                start_time = time.time()
                translation = self.translation_service.translate_text(content_text, chunk_size=chunk_size, delay=chunk_delay, progress_callback=progress_callback)
                translation_time = time.time() - start_time
                if translation:
                    update_dynamic_wpm(self.settings_manager, engine, article.get('word_count', 0) or 0, translation_time)
                self.after(0, lambda: self._on_translation_complete(article_id, translation))
            except Exception as e:
                print(f"[Translation Worker Error] {e}")
                self.after(0, lambda: self._on_translation_complete(article_id, None))

        threading.Thread(target=worker, daemon=True).start()

    def _tick_translation_timer(self):
        if not hasattr(self, 'loading_win') or not self.loading_win.winfo_exists():
            return
        elapsed = time.time() - self._translation_start_time
        self.timer_label.configure(text=f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}")
        self.loading_win.after(1000, self._tick_translation_timer)

    def _on_translation_complete(self, article_id: int, translation: str):
        if hasattr(self, 'loading_win') and self.loading_win.winfo_exists():
            self.loading_win.destroy()
        if translation:
            self.db_manager.update_article_translation(article_id, translation, 'translated')
            show_info(self, "Thành công", "Dịch thành công! Bản dịch đã được lưu.")
            self._render_content()
            self._refresh_eta()
        else:
            show_error(self, "Lỗi", "Dịch thất bại. Vui lòng kiểm tra API Key và thử lại.")

    def _refresh_eta(self):
        if not self.winfo_exists() or not hasattr(self, 'lbl_eta') or not self.lbl_eta.winfo_exists():
            return
        fresh_data = self.db_manager.get_book_details(self.book_id)
        if not fresh_data:
            return
        engine = self.settings_manager.get("translation_engine", "cloud")
        wpm = int(self.settings_manager.get(f"{engine}_llm_wpm", 6000 if engine == "cloud" else 180))
        eta_text = calculate_book_eta(fresh_data.get('chapters', []), wpm=wpm, engine=engine)
        self.lbl_eta.configure(text=f"⏱ Ước tính dịch: {eta_text}")

    # ─────────────────────────────────────────────────────────────────
    # Variant Transformation
    # ─────────────────────────────────────────────────────────────────

    def _transform_article(self, article, variant_type: str):
        if not self.translation_service.api_key:
            show_warning(self, "Thiếu API Key", "Vui lòng nhập API Key trong phần Cài đặt trước.")
            return
        archive_text = article.get('translation_text', '')
        if not archive_text:
            show_warning(self, "Chưa có bản dịch", "Cần dịch lưu trữ trước khi chuyển thể.")
            return

        article_id = article['id']
        original_text = self.db_manager.get_article_content(article_id) or ''
        label = {'website': 'Website', 'facebook': 'Facebook'}.get(variant_type, variant_type)

        self.loading_win = ctk.CTkToplevel(self)
        self.loading_win.title(f"Chuyển thể → {label}")
        self.loading_win.geometry("350x100")
        self.loading_win.transient(self)
        self.loading_win.grab_set()
        ctk.CTkLabel(self.loading_win, text=f"Đang tạo bản {label}...", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(pady=(25, 5))
        self.progress_bar = ctk.CTkProgressBar(self.loading_win, mode="indeterminate")
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_bar.start()

        def worker():
            result, err = self.translation_service.transform_text(archive_text, original_text, variant_type)
            self.after(0, lambda: self._on_transform_complete(article_id, variant_type, result, err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_transform_complete(self, article_id, variant_type, result, error):
        if hasattr(self, 'loading_win') and self.loading_win.winfo_exists():
            self.loading_win.destroy()
        label = {'website': 'Website', 'facebook': 'Facebook'}.get(variant_type, variant_type)
        if result:
            self.db_manager.update_article_variant(article_id, variant_type, result)
            show_info(self, "Thành công", f"Bản {label} đã được tạo và lưu!")
            self._render_content()
        else:
            show_error(self, "Lỗi", f"Chuyển thể {label} thất bại: {error}")

    # ─────────────────────────────────────────────────────────────────
    # Dual View Editor
    # ─────────────────────────────────────────────────────────────────

    def _open_dual_view(self, article):
        content_text = self.db_manager.get_article_content(article['id'])
        full_article = article.copy()
        full_article['content_text'] = content_text
        editor = DualViewEditor(self, full_article, self._save_translation_update, self.db_manager)
        editor.grab_set()

    def _save_translation_update(self, article_id, new_text):
        self.db_manager.update_article_translation(article_id, new_text, 'translated')
        self._render_content()

    # ─────────────────────────────────────────────────────────────────
    # Webview
    # ─────────────────────────────────────────────────────────────────

    def _generate_and_open_webview(self):
        try:
            output_dir = get_user_data_dir() / "webviews" / str(self.book_id)
            images_dir = output_dir / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            full_chapters = []
            for chap_lite in self.chapters:
                full_articles = []
                for art_lite in chap_lite.get('articles', []):
                    art_id = art_lite['id']
                    content = self.db_manager.get_article_content(art_id)
                    trans = art_lite.get('translation_text', '')
                    for img in self.db_manager.get_article_images(art_id):
                        src_path = Path(img['path'])
                        if src_path.exists():
                            dest = images_dir / src_path.name
                            if not dest.exists():
                                try:
                                    shutil.copy2(src_path, dest)
                                except Exception:
                                    pass
                    full_articles.append({'subtitle': art_lite.get('subtitle'), 'content_text': content, 'translation_text': trans})
                full_chapters.append({'title': chap_lite.get('title'), 'articles': full_articles})

            index_path = webview_generator.generate_webview(self.title(), "Author", full_chapters, output_dir)
            webbrowser.open(index_path.resolve().as_uri())
        except Exception as e:
            show_error(self, "Lỗi Webview", f"Không thể tạo webview: {e}")
