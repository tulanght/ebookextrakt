# file-path: src/extract_app/core/content_structurer.py
# version: 1.2 (Pylint Compliance)
# last-updated: 2025-09-27
# description: Cleans up the PDF content structurer module to meet Pylint standards.

"""
PDF Content Structurer.

This module provides heuristics to analyze raw content extracted from a PDF
chapter and structure it into smaller, more meaningful articles based on
font size analysis to detect headings.
"""

from collections import Counter
from typing import Any, Dict, List


def _find_dominant_font_size(content: List) -> float:
    """Finds the most common font size in a list of text content items."""
    sizes = [
        item[1]['size'] for item in content
        if item[0] == 'text' and isinstance(item[1], dict) and item[1].get('size', 0) > 0
    ]
    if not sizes:
        return 12.0  # Return a default font size if none are found
    return Counter(sizes).most_common(1)[0][0]


# pylint: disable=too-many-locals
def structure_pdf_articles(chapter_content: List) -> List[Dict[str, Any]]:
    """
    Structures raw PDF chapter content into a list of articles.

    Args:
        chapter_content: A list of content tuples (type, data) from the PDF parser.

    Returns:
        A list of dictionaries, where each dictionary represents a structured article.
    """
    if not chapter_content:
        return []

    dominant_size = _find_dominant_font_size(chapter_content)
    heading_threshold = dominant_size * 1.15

    articles = []
    current_article_content = []
    current_subtitle = ""

    # Check if any headings are present based on the font size threshold
    headings_found = any(
        item[0] == 'text' and isinstance(item[1], dict) and
        item[1].get('size', 0) > heading_threshold
        for item in chapter_content
    )

    # If no headings are found, treat the entire chapter as a single article
    if not headings_found:
        return [{'subtitle': '', 'content': chapter_content}]

    # If headings exist, split the content into articles
    for content_type, data in chapter_content:
        is_heading = False
        if (content_type == 'text' and isinstance(data, dict) and
                data.get('size', 0) > heading_threshold):
            is_heading = True

        if is_heading:
            # Save the previous article if it has content
            if current_article_content:
                articles.append({
                    'subtitle': current_subtitle,
                    'content': current_article_content
                })
            # Start a new article
            current_subtitle = data.get('content', '')
            current_article_content = []
        else:
            current_article_content.append((content_type, data))

    # Append the last remaining article
    if current_article_content:
        articles.append({
            'subtitle': current_subtitle,
            'content': current_article_content
        })

    return articles