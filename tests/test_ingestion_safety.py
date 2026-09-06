# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: tests/test_ingestion_safety.py
# Version: 1.1.0
# Author: Codex
# Description: Regression tests for ingestion worker wiring and recoverable cleanup.
# --------------------------------------------------------------------------------

"""Regression tests for destructive and asynchronous ingestion boundaries."""

import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

from packaging.requirements import Requirement

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


def test_ingestion_never_falls_back_to_permanent_unlink() -> None:
    """Ingestion cleanup paths must not permanently unlink source ebooks."""
    source = inspect.getsource(IngestionView)

    assert ".unlink(" not in source


def test_single_worker_does_not_treat_source_as_duplicate(tmp_path: Path) -> None:
    """Reclassifying an in-place ebook must preserve it and update its DB row."""
    source = tmp_path / "Biology" / "Birds" / "Canonical Book.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"pdf content")

    view = MagicMock()
    view.lib_dir = tmp_path
    view._get_sample_text.return_value = "TABLE OF CONTENTS"
    view.ai_classifier.analyze_book.return_value = {
        "title": "Canonical Book",
        "author": "",
        "year": 2026,
    }
    connection = view.db_manager._get_connection.return_value

    with (
        patch(
            "src.extract_app.modules.ui.ingestion_view.load_overrides",
            return_value={},
        ),
        patch(
            "src.extract_app.modules.ui.ingestion_view.classify_file",
            return_value="Birds",
        ),
    ):
        IngestionView._clean_single_worker(view, source, {"id": 42})

    view._quarantine_file.assert_not_called()
    connection.cursor.return_value.execute.assert_called_once()
    assert source.exists()


def test_batch_ai_does_not_treat_source_as_duplicate(tmp_path: Path) -> None:
    """Batch classification must exclude the current file from duplicate lookup."""
    source = tmp_path / "Biology" / "Birds" / "Canonical Book.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"pdf content")

    view = MagicMock()
    view.lib_dir = tmp_path
    view.clean_files = [
        {"path": str(source), "name": source.name, "ext": "pdf"},
    ]
    view._cancel_scan = False
    view._get_sample_text.return_value = "TABLE OF CONTENTS"
    view.ai_classifier.cloud_client.is_ready = True
    view.ai_classifier.analyze_book.return_value = {
        "title": "Canonical Book",
        "author": "",
        "year": 2026,
    }
    view.db_manager.get_all_books.return_value = []

    with (
        patch(
            "src.extract_app.modules.ui.ingestion_view.load_overrides",
            return_value={},
        ),
        patch(
            "src.extract_app.modules.ui.ingestion_view.classify_file",
            return_value="Birds",
        ),
        patch("src.extract_app.modules.ui.ingestion_view.send2trash") as trash,
    ):
        IngestionView._ai_worker(view)

    trash.assert_not_called()
    assert source.exists()


def test_remove_book_recycles_file_before_committing_database_delete() -> None:
    """Catalog deletion must only commit after recoverable file cleanup succeeds."""
    events: list[str] = []
    view = MagicMock()
    connection = view.db_manager._get_connection.return_value
    cursor = connection.cursor.return_value
    cursor.execute.side_effect = lambda *args: events.append("database-delete")
    connection.commit.side_effect = lambda: events.append("database-commit")

    with patch(
        "src.extract_app.modules.ui.ingestion_view.send2trash",
        side_effect=lambda path: events.append("recycle"),
    ):
        IngestionView._remove_and_quarantine(
            view,
            book_id=42,
            file_path=Path("book.pdf"),
            row_widget=MagicMock(),
        )

    assert events == ["recycle", "database-delete", "database-commit"]


def test_remove_book_preserves_database_when_recycle_bin_fails() -> None:
    """A failed Recycle Bin operation must leave the catalog row untouched."""
    view = MagicMock()
    connection = view.db_manager._get_connection.return_value

    with patch(
        "src.extract_app.modules.ui.ingestion_view.send2trash",
        side_effect=OSError("Recycle Bin unavailable"),
    ):
        IngestionView._remove_and_quarantine(
            view,
            book_id=42,
            file_path=Path("book.pdf"),
            row_widget=MagicMock(),
        )

    connection.cursor.return_value.execute.assert_not_called()
    connection.commit.assert_not_called()


def test_send2trash_is_declared_as_runtime_dependency() -> None:
    """A clean environment must install the ingestion cleanup dependency."""
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    requirements = {
        Requirement(line).name.lower()
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "send2trash" in requirements
