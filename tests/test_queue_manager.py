import pytest
from unittest.mock import Mock, call
import time
from src.extract_app.core.queue_manager import ChapterQueueManager, ChapterQueueItem, QueueStatus

@pytest.fixture
def mock_deps():
    translation_service = Mock()
    # Mock successful translation by default
    translation_service.translate_text.return_value = "Translated Text"
    
    db_manager = Mock()
    settings_manager = Mock()
    settings_manager.get.side_effect = lambda key, default=None: default
    
    return translation_service, db_manager, settings_manager

@pytest.fixture
def queue_manager(mock_deps):
    ts, db, sm = mock_deps
    qm = ChapterQueueManager(
        translation_service=ts,
        db_manager=db,
        settings_manager=sm,
        on_item_done=Mock(),
        on_queue_done=Mock(),
        on_status_change=Mock()
    )
    yield qm
    qm.stop()  # Ensure thread stops after test

def test_initialization(queue_manager):
    assert queue_manager.status == QueueStatus.IDLE
    assert len(queue_manager.pending_ids) == 0

def test_enqueue(queue_manager):
    item = ChapterQueueItem(1, "Subtitle", 100, "Content")
    queue_manager.enqueue(item)
    assert len(queue_manager.pending_ids) == 1
    assert queue_manager.is_queued(1)
    
    # Enqueue same item shouldn't duplicate in pending_ids
    queue_manager.enqueue(item)
    assert len(queue_manager.pending_ids) == 1

def test_remove(queue_manager):
    item = ChapterQueueItem(1, "Subtitle", 100, "Content")
    queue_manager.enqueue(item)
    
    assert queue_manager.remove(1) is True
    assert not queue_manager.is_queued(1)
    
    assert queue_manager.remove(2) is False

def test_clear(queue_manager):
    item1 = ChapterQueueItem(1, "Subtitle 1", 100, "Content")
    item2 = ChapterQueueItem(2, "Subtitle 2", 100, "Content")
    queue_manager.enqueue(item1)
    queue_manager.enqueue(item2)
    
    assert len(queue_manager.pending_ids) == 2
    queue_manager.clear()
    assert len(queue_manager.pending_ids) == 0

def test_status_transitions(queue_manager):
    queue_manager.start()
    assert queue_manager.status == QueueStatus.RUNNING
    queue_manager.on_status_change.assert_called_with(QueueStatus.RUNNING)
    
    queue_manager.pause()
    assert queue_manager.status == QueueStatus.PAUSED
    queue_manager.on_status_change.assert_called_with(QueueStatus.PAUSED)
    
    queue_manager.resume()
    assert queue_manager.status == QueueStatus.RUNNING

def test_worker_processing(queue_manager, mock_deps):
    ts, db, sm = mock_deps
    
    item1 = ChapterQueueItem(1, "S1", 100, "C1")
    item2 = ChapterQueueItem(2, "S2", 200, "C2")
    
    queue_manager.enqueue(item1)
    queue_manager.enqueue(item2)
    
    queue_manager.start()
    
    # Wait for worker thread to finish processing and timeout gracefully
    if queue_manager._worker_thread:
        queue_manager._worker_thread.join(timeout=2.0)
    
    assert queue_manager.status == QueueStatus.IDLE
    assert len(queue_manager.pending_ids) == 0
    
    # Verify translation called twice
    assert ts.translate_text.call_count == 2
    
    # Verify DB update called twice
    assert db.update_article_translation.call_count == 2
    db.update_article_translation.assert_has_calls([
        call(1, "Translated Text", "translated"),
        call(2, "Translated Text", "translated")
    ])
    
    # Verify callbacks
    assert queue_manager.on_item_done.call_count == 2
    queue_manager.on_queue_done.assert_called_once()

def test_worker_translation_failure(queue_manager, mock_deps):
    ts, db, sm = mock_deps
    # Simulate a failure returning None
    ts.translate_text.return_value = None
    
    item = ChapterQueueItem(1, "S1", 100, "C1")
    queue_manager.enqueue(item)
    
    queue_manager.start()
    if queue_manager._worker_thread:
        queue_manager._worker_thread.join(timeout=2.0)
    
    assert len(queue_manager.pending_ids) == 0
    # DB update should NOT be called
    db.update_article_translation.assert_not_called()
    
    # Callback should be fired with False
    queue_manager.on_item_done.assert_called_once_with(1, False)

def test_stop_aborts_queue(queue_manager):
    item1 = ChapterQueueItem(1, "S1", 100, "C1")
    item2 = ChapterQueueItem(2, "S2", 200, "C2")
    queue_manager.enqueue(item1)
    queue_manager.enqueue(item2)
    
    queue_manager.stop()
    assert queue_manager.status == QueueStatus.IDLE
    assert len(queue_manager.pending_ids) == 0
