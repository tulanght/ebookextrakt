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
    for element in tags:
        if not isinstance(element, Tag):
            continue
        temp_soup = BeautifulSoup(str(element), 'xml')
        temp_tag = temp_soup.find(element.name)
        if not temp_tag:
            continue
        
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
                    # Try to find caption (complex if we re-parsed just the img)
                    # For direct img, we might have lost the figure context if we only passed the img tag.
                    # But SmartSplitter tries to pass containers.
                    caption = ""
                    if img_tag.parent and img_tag.parent.name == 'figure':
                         caption_tag = img_tag.parent.find('figcaption')
                         if caption_tag:
                             caption = caption_tag.get_text(strip=True)

                    content_list.append(
                        ('image', {'anchor': anchor, 'caption': caption}))
            
            # Decompose to remove from text
            # If temp_tag IS the image, decomposing it might be weird if we access it later?
            # But we only access .get_text() later.
            if img_tag != temp_tag:
                 img_tag.decompose()
        
        # If the top tag was an image and we processed it, text will be empty/irrelevant.
        if temp_tag.name == 'img':
             continue
             
        text = temp_tag.get_text(strip=True)
        text = temp_tag.get_text(strip=True)
        if text:
            content_list.append(('text', text))
    return content_list