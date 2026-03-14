# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/queue_manager.py
# Version: 1.0.0
# Author: Antigravity
# Description: Chapter-level translation queue manager with background thread worker.
# --------------------------------------------------------------------------------

import time
import threading
import queue
import logging
from typing import Optional, Callable, List, Dict, Any

from .eta_calculator import update_dynamic_wpm

logger = logging.getLogger(__name__)


class QueueStatus:
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


class ChapterQueueItem:
    """Represents a single article/chapter enqueued for translation."""

    def __init__(self, article_id: int, subtitle: str, word_count: int, content: str):
        self.article_id = article_id
        self.subtitle = subtitle
        self.word_count = word_count
        self.content = content

    def __repr__(self) -> str:
        return f"<QueueItem id={self.article_id} '{self.subtitle[:30]}' {self.word_count}w>"


class ChapterQueueManager:
    """
    Manages a chapter-level translation queue for a single book.

    The queue processes articles sequentially in a background daemon thread.
    UI updates are dispatched safely via the `ui_callback` mechanism using
    `widget.after(0, fn)` from the calling view.

    Args:
        translation_service: The app's `TranslationService` instance.
        db_manager:          The app's `DatabaseManager` instance.
        settings_manager:    The app's `SettingsManager` instance.
        on_item_done:        Callback(article_id, success) fired on each completion.
        on_queue_done:       Callback() fired when the entire queue is empty.
        on_status_change:    Callback(status: str) fired when queue status changes.
    """

    def __init__(
        self,
        translation_service,
        db_manager,
        settings_manager,
        on_item_done: Optional[Callable[[int, bool], None]] = None,
        on_queue_done: Optional[Callable[[], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
    ):
        self.translation_service = translation_service
        self.db_manager = db_manager
        self.settings_manager = settings_manager

        self.on_item_done = on_item_done
        self.on_queue_done = on_queue_done
        self.on_status_change = on_status_change

        self._queue: queue.Queue[ChapterQueueItem] = queue.Queue()
        self._pending_ids: List[int] = []   # Ordered list of article_ids still queued
        self._lock = threading.Lock()        # Protects _pending_ids

        self._status: str = QueueStatus.IDLE
        self._pause_event = threading.Event()
        self._pause_event.set()             # Un-paused initially (set = not paused)
        self._stop_event = threading.Event()

        self._worker_thread: Optional[threading.Thread] = None
        self._current_item: Optional[ChapterQueueItem] = None
        self.done_count: int = 0  # Tracks items translated in current session

    # ─────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────

    @property
    def status(self) -> str:
        return self._status

    @property
    def pending_ids(self) -> List[int]:
        """Thread-safe snapshot of queued article ids."""
        with self._lock:
            return list(self._pending_ids)

    @property
    def current_article_id(self) -> Optional[int]:
        item = self._current_item
        return item.article_id if item else None

    def enqueue(self, item: ChapterQueueItem) -> None:
        """Add a chapter to the translation queue."""
        with self._lock:
            if item.article_id not in self._pending_ids:
                self._pending_ids.append(item.article_id)
                self._queue.put(item)
                logger.info(f"Enqueued: {item}")

    def remove(self, article_id: int) -> bool:
        """
        Remove an article from the queue.
        If it's currently being translated, it will finish first.

        Returns:
            True if the article was found and removed from the pending list.
        """
        with self._lock:
            if article_id in self._pending_ids:
                self._pending_ids.remove(article_id)
                logger.info(f"Removed article_id={article_id} from queue")
                return True
        return False

    def is_queued(self, article_id: int) -> bool:
        """Check if an article_id is in the queue (pending)."""
        with self._lock:
            return article_id in self._pending_ids

    def start(self) -> None:
        """Start the background worker if not already running."""
        if self._status == QueueStatus.RUNNING:
            return
        self._stop_event.clear()
        self._pause_event.set()  # ensure un-paused
        self.done_count = 0  # Reset counter for this session
        self._set_status(QueueStatus.RUNNING)
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._worker_thread = threading.Thread(
                target=self._worker_loop, daemon=True, name="ChapterQueueWorker"
            )
            self._worker_thread.start()
            logger.info("ChapterQueueWorker started")

    def pause(self) -> None:
        """Pause after the current article finishes."""
        if self._status == QueueStatus.RUNNING:
            self._pause_event.clear()
            self._set_status(QueueStatus.PAUSED)
            logger.info("Queue paused")

    def resume(self) -> None:
        """Resume a paused queue."""
        if self._status == QueueStatus.PAUSED:
            self._pause_event.set()
            self._set_status(QueueStatus.RUNNING)
            logger.info("Queue resumed")

    def stop(self) -> None:
        """Stop the queue gracefully after current article finishes."""
        self._stop_event.set()
        self._pause_event.set()  # unblock if paused so thread can exit
        with self._lock:
            self._pending_ids.clear()
        # Drain the internal queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break
        self._set_status(QueueStatus.IDLE)
        self.done_count = 0  # Reset on stop
        logger.info("Queue stopped and cleared")

    def clear(self) -> None:
        """Remove all pending (un-started) items from the queue."""
        with self._lock:
            self._pending_ids.clear()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break
        logger.info("Queue cleared")

    # ─────────────────────────────────────────────────────────────────
    # Internal Worker
    # ─────────────────────────────────────────────────────────────────

    def _worker_loop(self) -> None:
        """Main loop running on the background daemon thread."""
        logger.info("Worker loop started")
        while not self._stop_event.is_set():
            # Wait for un-pause
            self._pause_event.wait()

            if self._stop_event.is_set():
                break

            try:
                item: ChapterQueueItem = self._queue.get(timeout=0.5)
            except queue.Empty:
                # Queue is empty — we're done
                self._current_item = None
                self._set_status(QueueStatus.IDLE)
                if self.on_queue_done:
                    self.on_queue_done()
                logger.info("Queue exhausted, worker idle")
                break

            # Check if this item was removed while waiting
            with self._lock:
                if item.article_id not in self._pending_ids:
                    logger.info(f"Skipping removed item: {item}")
                    self._queue.task_done()
                    continue

            self._current_item = item
            logger.info(f"Translating: {item}")
            success = self._translate_item(item)

            # After translation, remove from pending list
            with self._lock:
                if item.article_id in self._pending_ids:
                    self._pending_ids.remove(item.article_id)

            self._current_item = None
            self._queue.task_done()
            self.done_count += 1  # Increment completed count

            if self.on_item_done:
                self.on_item_done(item.article_id, success)

        logger.info("Worker loop exited")

    def _translate_item(self, item: ChapterQueueItem) -> bool:
        """
        Executes translation for a single item. Runs on the worker thread.

        Returns:
            True if translation succeeded and was saved, False otherwise.
        """
        try:
            chunk_size = self.settings_manager.get("chunk_size", 3000)
            chunk_delay = self.settings_manager.get("chunk_delay", 2.0)
            engine = self.settings_manager.get("translation_engine", "cloud")

            start_time = time.time()
            translation = self.translation_service.translate_text(
                item.content,
                chunk_size=chunk_size,
                delay=chunk_delay,
            )
            translation_time = time.time() - start_time

            if translation:
                self.db_manager.update_article_translation(
                    item.article_id, translation, "translated"
                )
                logger.info(f"Saved translation for article_id={item.article_id}")
                
                update_dynamic_wpm(
                    self.settings_manager, engine,
                    item.word_count, translation_time
                )
                
                return True
            else:
                logger.warning(f"Translation returned None for article_id={item.article_id}")
                return False

        except Exception as e:
            logger.error(f"Queue worker error on article_id={item.article_id}: {e}")
            return False

    def _set_status(self, new_status: str) -> None:
        self._status = new_status
        if self.on_status_change:
            self.on_status_change(new_status)
