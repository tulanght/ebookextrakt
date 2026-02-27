# file-path: src/extract_app/core/epub_parsers/utils.py
# version: 1.0
# last-updated: 2025-09-27
# description: Shared utility functions for EPUB parsers to avoid code duplication..

"""
Shared utility functions for EPUB parsers.

This module contains common helper functions used by different EPUB parsing
strategies to handle tasks like saving images, resolving paths, and extracting
content from tags. This avoids code duplication and improves maintainability.
"""

import os
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup, Tag
from ebooklib import epub


def save_image_to_temp(image_item, temp_image_dir: Path, prefix="epub_") -> str:
    """Saves an image item to a temporary directory and returns its path."""
    image_bytes = image_item.get_content()
    image_filename = f"{prefix}{Path(image_item.get_name()).name}"
    image_path = temp_image_dir / image_filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    return str(image_path)


def resolve_image_path(src: str, doc_item: epub.EpubHtml, book: epub.EpubBook):
    """Resolves the absolute path of an image given its relative src."""
    if not src:
        return None
    current_dir = Path(doc_item.get_name()).parent
    resolved_path_str = os.path.normpath(
        os.path.join(current_dir, src)).replace('\\', '/')
    return book.get_item_with_href(resolved_path_str)


def extract_content_from_tags(
    tags: List[Tag], book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path
) -> List:
    """Extracts text and image data from a list of BeautifulSoup tags."""
    content_list = []
    
    # Collect heading titles to detect duplicate captions
    heading_titles = set()
    
    for element in tags:
        if not isinstance(element, Tag):
            continue
        temp_soup = BeautifulSoup(str(element), 'xml')
        temp_tag = temp_soup.find(element.name)
        if not temp_tag:
            continue
        
        # --- Phase 7: Remove junk HTML elements ---
        # Decompose nav, aside, footer, and toc-related elements
        for junk_tag in temp_tag.find_all(['nav', 'aside', 'footer']):
            junk_tag.decompose()
        # Also remove elements with toc-related IDs/classes
        for junk_tag in temp_tag.find_all(attrs={'id': lambda x: x and 'toc' in x.lower()}):
            junk_tag.decompose()
        for junk_tag in temp_tag.find_all(attrs={'class': lambda x: x and any('toc' in c.lower() for c in (x if isinstance(x, list) else [x]))}):
            junk_tag.decompose()
        for junk_tag in temp_tag.find_all(attrs={'epub:type': lambda x: x and 'toc' in x.lower()}):
            junk_tag.decompose()
        
        # Check if the tag itself is an image
        images_to_process = temp_tag.find_all('img')
        if temp_tag.name == 'img':
            images_to_process.append(temp_tag)
            
        for img_tag in images_to_process:
            if img_tag.get('src'):
                image_item = resolve_image_path(
                    img_tag.get('src'), doc_item, book)
                if image_item:
                    anchor = save_image_to_temp(
                        image_item, temp_image_dir)
                    
                    # --- Phase 7: Clean messy captions ---
                    caption = ""
                    if img_tag.parent and img_tag.parent.name == 'figure':
                         caption_tag = img_tag.parent.find('figcaption')
                         if caption_tag:
                              raw_caption = caption_tag.get_text(strip=True)
                              # Only skip if caption is an exact duplicate of a heading title
                              if any(raw_caption.lower().strip() == h.lower().strip() for h in heading_titles if h):
                                  caption = ""
                              else:
                                  caption = raw_caption

                    content_list.append(
                        ('image', {'anchor': anchor, 'caption': caption}))
            
            # Decompose to remove from text
            if img_tag != temp_tag:
                 img_tag.decompose()
        
        # If the top tag was an image and we processed it, text will be empty/irrelevant.
        if temp_tag.name == 'img':
             continue
             
        # Smart text extraction: preserve paragraph structure
        raw_text = temp_tag.get_text(separator='\n')
        lines_txt = [line.strip() for line in raw_text.split('\n')]
        lines_txt = [line for line in lines_txt if line]
        text = ' '.join(lines_txt)
        
        if text:
            # Formatting Preservation: Headings
            if temp_tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                try:
                    level = int(temp_tag.name[1])
                    prefix = '#' * level
                    text = f"{prefix} {text}"
                    # Track heading text for caption dedup
                    heading_titles.add(text.lstrip('# ').strip())
                except:
                    pass
                     
            content_list.append(('text', text))
    return content_list
