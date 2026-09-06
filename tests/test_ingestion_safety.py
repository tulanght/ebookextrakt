# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: tests/test_ingestion_safety.py
# Version: 1.0.0
# Author: Codex
# Description: Regression tests for ingestion worker wiring and recoverable cleanup.
# --------------------------------------------------------------------------------

"""Regression tests for destructive and asynchronous ingestion boundaries."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.extract_app.modules.ui.ingestion_view import IngestionView


def test_clean_single_worker_is_available() -> None:
    """Queued single-file cleanup must resolve to a real worker method."""
    assert hasattr(IngestionView, "_clean_single_worker")
    assert callable(getattr(IngestionView, "_clean_single_worker", None))


def test_quarantine_keeps_file_when_recycle_bin_fails(tmp_path: Path) -> None:
    """A Recycle Bin failure must never fall back to permanent deletion."""
    ebook = tmp_path / "valuable-book.epub"
    ebook.write_bytes(b"ebook content")
    view = MagicMock()

    with patch(
        "src.extract_app.modules.ui.ingestion_view.send2trash",
        side_effect=OSError("Recycle Bin unavailable"),
    ):
        IngestionView._quarantine_file(view, ebook)

    assert ebook.exists()
    view._insert_log.assert_called_once()
    assert "LỖI" in view._insert_log.call_args.args[0]


def test_quarantine_uses_recycle_bin_on_success(tmp_path: Path) -> None:
    """Normal cleanup delegates to send2trash and reports completion."""
    ebook = tmp_path / "duplicate-book.pdf"
    ebook.write_bytes(b"pdf content")
    view = MagicMock()

    with patch("src.extract_app.modules.ui.ingestion_view.send2trash") as trash:
        IngestionView._quarantine_file(view, ebook)

    trash.assert_called_once_with(str(ebook).replace("/", "\\"))
    view._insert_log.assert_called_once()
    assert "[XÓA]" in view._insert_log.call_args.args[0]
