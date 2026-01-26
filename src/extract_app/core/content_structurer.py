# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/content_structurer.py
# Version: 1.3.0
# Author: Antigravity
# Description: Structure content into articles. Supports PDF (font analysis) and EPUB (HTML headers).
# --------------------------------------------------------------------------------

import re
from collections import Counter
from typing import List, Dict, Any, Tuple, Union
from bs4 import BeautifulSoup, Tag

class SmartSplitter:
    """
    Splits HTML content into meaningful articles based on headers.
    Used primarily for EPUB parsing where we have raw HTML.
    """
    
    @staticmethod
    def split_by_headers(html_content: str, min_words: int = 50) -> List[Dict[str, Any]]:
        """
        Parses HTML and splits it into sections when headers (h1-h4) are found.
        (Returns processed content strings/dicts)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        # This legacy method returns extracted content.
        # Ideally we move to using split_soup_to_sections everywhere.
        return SmartSplitter._soup_split(soup)

    @staticmethod
    def split_soup_to_sections(soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Splits soup into sections based on h1-h4 tags, returning lists of TAGS.
        Format: [{'subtitle': 'Header', 'tags': [Tag, Tag...]}]
        """
        sections = []
        current_tags = []
        current_title = "Nội dung" # Default title
        
        elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'img', 'div', 'ul', 'ol', 'blockquote', 'table'])
        
        processed = set()
        
        for p in elements:
            if p in processed:
                continue
                
            # If it's a header, switch context
            if p.name in ['h1', 'h2', 'h3', 'h4']:
                text = p.get_text(strip=True)
                if text:
                    # Save previous section
                    if current_tags:
                        sections.append({'subtitle': current_title, 'tags': current_tags})
                        current_tags = []
                    current_title = text
                    # Header itself is NOT added to content tags of the new section
                    # (It is the subtitle)
                    processed.add(p)
                    for child in p.descendants:
                        processed.add(child)
                continue
            
            # Add to current tags
            current_tags.append(p)
            processed.add(p)
            # If it's a container, mark descendants as processed so we don't re-add them
            if hasattr(p, 'descendants'):
                for child in p.descendants:
                    processed.add(child)
        
        # Add the last accumulated section
        if current_tags:
            sections.append({'subtitle': current_title, 'tags': current_tags})
            
        return sections

    @staticmethod
    def _soup_split(soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Splits soup into articles based on h1-h4 tags.
        """
        articles = []
        current_content = []
        current_title = "Nội dung" # Default title
        
        # We flatten the structure to process it linearly.
        # We care about: Headers, Paragraphs, Images, Lists, Divs.
        # We rely on BeautifulSoup's findingall to get them in document order.
        elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'img', 'div', 'ul', 'ol', 'blockquote'])
        
        processed = set()
        
        for p in elements:
            if p in processed:
                continue
                
            # If it's a header, switch context
            if p.name in ['h1', 'h2', 'h3', 'h4']:
                text = p.get_text(strip=True)
                if text:
                    # Save previous article
                    if current_content:
                        articles.append({'subtitle': current_title, 'content': current_content})
                        current_content = []
                    current_title = text
                    
                    # Mark header and its descendant contents as processed
                    processed.add(p)
                    for child in p.descendants:
                        processed.add(child)
                continue
                
            # If it's an image
            if p.name == 'img':
                src = p.get('src')
                alt = p.get('alt', '')
                if src:
                    current_content.append(('image', {'anchor': src, 'caption': alt}))
                processed.add(p)
                continue

            # If it's text container
            if p.name in ['p', 'div', 'li', 'blockquote']:
                # Ensure it's not a container for other block elements we will visit later
                if p.find(['p', 'div', 'ul', 'ol', 'blockquote', 'h1', 'h2', 'h3', 'h4']):
                    continue 
                
                text = p.get_text(separator=" ", strip=True)
                if len(text) > 1: # Ignore empty/tiny
                    current_content.append(('text', text))
                processed.add(p)
        
        # Add the last accumulated article
        if current_content:
            articles.append({'subtitle': current_title, 'content': current_content})
            
        return [a for a in articles if a['content']]

# --- Legacy/PDF Support Functions ---

def _find_dominant_font_size(content: List) -> float:
    """Finds the most common font size in a list of text content items."""
    sizes = [
        item[1]['size'] for item in content
        if item[0] == 'text' and isinstance(item[1], dict) and item[1].get('size', 0) > 0
    ]
    if not sizes:
        return 12.0
    return Counter(sizes).most_common(1)[0][0]

def structure_pdf_articles(chapter_content: List) -> List[Dict[str, Any]]:
    """
    Structures raw PDF chapter content into a list of articles based on font size heuristics.
    RESTORED LOGIC.
    """
    if not chapter_content:
        return []

    dominant_size = _find_dominant_font_size(chapter_content)
    heading_threshold = dominant_size * 1.15

    articles = []
    current_article_content = []
    current_subtitle = ""

    headings_found = any(
        item[0] == 'text' and isinstance(item[1], dict) and
        item[1].get('size', 0) > heading_threshold
        for item in chapter_content
    )

    if not headings_found:
        return [{'subtitle': '', 'content': chapter_content}]

    for content_type, data in chapter_content:
        is_heading = False
        if (content_type == 'text' and isinstance(data, dict) and
                data.get('size', 0) > heading_threshold):
            is_heading = True

        if is_heading:
            if current_article_content:
                articles.append({'subtitle': current_subtitle, 'content': current_article_content})
            current_subtitle = data.get('content', '')
            current_article_content = []
        else:
            current_article_content.append((content_type, data))

    if current_article_content:
        articles.append({'subtitle': current_subtitle, 'content': current_article_content})

    return articles