# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/eta_calculator.py
# Version: 1.0.0
# Author: Antigravity
# Description: Utility functions for estimating translation time for books.
# --------------------------------------------------------------------------------

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def update_dynamic_wpm(settings_manager, engine: str, word_count: int, elapsed_seconds: float) -> None:
    """
    Updates the WPM setting using an Exponential Weighted Moving Average (EWMA).
    
    Called after each successful translation to learn the real speed of the engine.
    Blends 70% of the saved WPM with 30% of the freshly observed WPM.
    """
    if elapsed_seconds <= 0 or word_count <= 0:
        return
    wpm_key = f"{engine}_llm_wpm"
    default_wpm = 6000 if engine == "cloud" else 180
    saved_wpm = int(settings_manager.get(wpm_key, default_wpm))
    real_wpm = int((word_count / elapsed_seconds) * 60)
    new_wpm = max(1, int((saved_wpm * 0.7) + (real_wpm * 0.3)))
    settings_manager.set(wpm_key, new_wpm)
    logger.info(f"Dynamic WPM ({engine}): {saved_wpm} -> {new_wpm} (Real: {real_wpm})")


def calculate_book_eta(chapters: List[Dict[str, Any]], wpm: int = 180, engine: str = "") -> str:
    """
    Calculates the estimated time remaining to translate all untranslated articles in a book.

    Args:
        chapters: List of chapter dicts from `db_manager.get_book_details()`.
                  Each chapter has an 'articles' key with article dicts.
                  Each article has 'word_count' (int) and 'status' (str).
        wpm: Words per minute speed of the Local/Cloud LLM (default: 180).
        engine: "cloud" or "local" to append string context like "(Cloud)".

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
        res = "< 1 phút"
    else:
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)

        if hours > 0:
            res = f"~{hours}h {minutes:02d}m"
        else:
            res = f"~{minutes}m"
            
    if engine:
        engine_name = "Cloud" if engine.lower() == "cloud" else "Local"
        return f"{res} ({engine_name})"
        
    return res
