# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/eta_calculator.py
# Version: 1.0.0
# Author: Antigravity
# Description: Utility functions for estimating translation time for books.
# --------------------------------------------------------------------------------

from typing import Dict, Any, List


def calculate_book_eta(chapters: List[Dict[str, Any]], wpm: int = 180) -> str:
    """
    Calculates the estimated time remaining to translate all untranslated articles in a book.

    Args:
        chapters: List of chapter dicts from `db_manager.get_book_details()`.
                  Each chapter has an 'articles' key with article dicts.
                  Each article has 'word_count' (int) and 'status' (str).
        wpm: Words per minute speed of the Local LLM (default: 180).

    Returns:
        A formatted string like "~2h 15m" or "~45m" or "Đã dịch xong!" or "N/A".
    """
    if wpm <= 0:
        return "N/A"

    total_untranslated_words = 0

    for chapter in chapters:
        for article in chapter.get('articles', []):
            is_leaf = article.get('is_leaf', 1)
            status = article.get('status', 'new')
            word_count = article.get('word_count', 0) or 0

            # Only count leaf articles that haven't been translated yet
            if is_leaf and status != 'translated' and word_count > 0:
                total_untranslated_words += word_count

    if total_untranslated_words == 0:
        return "Đã dịch xong! ✅"

    total_minutes = total_untranslated_words / wpm

    if total_minutes < 1:
        return "< 1 phút"

    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)

    if hours > 0:
        return f"~{hours}h {minutes:02d}m"
    else:
        return f"~{minutes}m"
