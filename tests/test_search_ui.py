import pytest
from unittest.mock import MagicMock, patch
import customtkinter as ctk
import sys
import os

# Ensure the src path is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from extract_app.modules.ui.search_view import SearchView

@pytest.fixture
def mock_master():
    # Simple hidden root to avoid drawing to screen
    root = ctk.CTk()
    root.withdraw()
    yield root
    root.destroy()

@pytest.fixture
def mock_db_manager():
    return MagicMock()

@pytest.fixture
def search_view(mock_master, mock_db_manager):
    view = SearchView(master=mock_master, db_manager=mock_db_manager)
    return view

def test_search_view_init(search_view):
    """Test initial state of UI elements."""
    assert search_view.entry_search.get() == ""
    assert search_view.option_category.get() == "Tất cả"
    assert search_view.lbl_status.cget("text") == "Nhập từ khóa để tìm trong thư viện ebooks."
    assert len(search_view.result_cards) == 0

def test_search_view_render_empty(search_view):
    """Test rendering when no results are found."""
    search_view._render_results([], "query_str")
    
    # Needs to update status label appropriately
    assert "Không tìm thấy" in search_view.lbl_status.cget("text")
    assert "query_str" in search_view.lbl_status.cget("text")
    assert len(search_view.result_cards) == 0

def test_search_view_render_results(search_view):
    """Test rendering cards with mocked subset."""
    mock_results = [
        {
            "book_title": "Book 1",
            "chapter_title": "Chapter 1",
            "section_title": "Sec",
            "site_category": "animal",
            "snippet": "hello world",
            "passage": "detailed text"
        },
        {
            "book_title": "Book 2",
            "chapter_title": "",
            "section_title": "",
            "site_category": "plant",
            "snippet": "test plant",
            "passage": "foo bar"
        }
    ]
    
    search_view._render_results(mock_results, "query_str")
    
    assert len(search_view.result_cards) == 2
    
    # Check selection flow
    first_card = search_view.result_cards[0]
    
    # Manually trigger card select
    search_view._select_card(first_card, mock_results[0])
    
    assert search_view.lbl_book_title.cget("text") == "Book 1"
    assert search_view.lbl_breadcrumb.cget("text") == "Chapter 1 › Sec"
    assert "animal" in search_view.lbl_category_badge.cget("text")
    
    # The textbox should contain passage
    content_text = search_view.textbox_content.get("0.0", "end").strip()
    assert content_text == "detailed text"

def test_search_view_trigger_search(search_view, mock_db_manager):
    """Ensure search trigger queries DB correctly."""
    
    # Overwrite the wait time to execute immediately or mock thread
    with patch('threading.Thread') as mock_thread:
        search_view.entry_search.insert(0, "keyword")
        search_view.option_category.set("animal")
        
        # Trigger UI search
        search_view._on_search()
        
        # Status should immediately shift to loading
        assert search_view.lbl_status.cget("text") == "Đang tìm..."
        assert mock_thread.called
        
        # We can extract the target worker and execute it directly bypassing threading overhead
        target_worker = mock_thread.call_args[1].get('target')
        target_worker()
        
        mock_db_manager.search_content.assert_called_once_with(
            query="keyword",
            site_category="animal",
            limit=20,
            min_words=50
        )
