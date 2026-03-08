import pytest
from src.extract_app.core.eta_calculator import calculate_book_eta

def test_calculate_book_eta_empty():
    """Test with empty chapters list."""
    assert calculate_book_eta([]) == "Đã dịch xong! ✅"

def test_calculate_book_eta_all_translated():
    """Test when all articles are already translated."""
    chapters = [
        {
            "articles": [
                {"word_count": 500, "status": "translated", "is_leaf": 1},
                {"word_count": 1000, "status": "translated", "is_leaf": 1}
            ]
        }
    ]
    assert calculate_book_eta(chapters) == "Đã dịch xong! ✅"

def test_calculate_book_eta_ignores_parents():
    """Test that parent articles (is_leaf=0) are ignored."""
    chapters = [
        {
            "articles": [
                {"word_count": 1000, "status": "new", "is_leaf": 0},  # Ignored
                {"word_count": 500, "status": "translated", "is_leaf": 1} # Translated
            ]
        }
    ]
    assert calculate_book_eta(chapters) == "Đã dịch xong! ✅"

def test_calculate_book_eta_less_than_one_minute():
    """Test translation estimation < 1 minute."""
    chapters = [
        {
            "articles": [
                {"word_count": 100, "status": "new", "is_leaf": 1}
            ]
        }
    ]
    assert calculate_book_eta(chapters, wpm=180) == "< 1 phút"

def test_calculate_book_eta_minutes_only():
    """Test estimation with only minutes."""
    chapters = [
        {
            "articles": [
                {"word_count": 180 * 45, "status": "new", "is_leaf": 1} # 45 minutes
            ]
        }
    ]
    assert calculate_book_eta(chapters, wpm=180) == "~45m"

def test_calculate_book_eta_hours_and_minutes():
    """Test estimation with hours and minutes."""
    chapters = [
        {
            "articles": [
                {"word_count": 180 * 90, "status": "new", "is_leaf": 1} # 90 minutes = 1h 30m
            ]
        }
    ]
    assert calculate_book_eta(chapters, wpm=180) == "~1h 30m"

def test_calculate_book_eta_multiple_chapters():
    """Test summing word counts across multiple chapters and articles."""
    chapters = [
        {
            "articles": [
                {"word_count": 180 * 20, "status": "new", "is_leaf": 1}, # 20m
                {"word_count": 180 * 10, "status": "new", "is_leaf": 1}  # 10m
            ]
        },
        {
            "articles": [
                {"word_count": 180 * 30, "status": "new", "is_leaf": 1}, # 30m
                {"word_count": 180 * 100, "status": "translated", "is_leaf": 1} # Ignored
            ]
        }
    ]
    # Total = 60 minutes
    assert calculate_book_eta(chapters, wpm=180) == "~1h 00m"

def test_calculate_book_eta_zero_wpm():
    """Test with wpm <= 0."""
    chapters = [
        {
            "articles": [
                {"word_count": 500, "status": "new", "is_leaf": 1}
            ]
        }
    ]
    assert calculate_book_eta(chapters, wpm=0) == "N/A"
    assert calculate_book_eta(chapters, wpm=-10) == "N/A"
