# file-path: src/extract_app/core/epub_parser.py
# version: 66.2 (Pylint Compliance)
# last-updated: 2025-09-26
# description: Cleans up the dispatcher module to meet Pylint standards.

"""
EPUB Parser Dispatcher.

This module acts as the main entry point for parsing EPUB files. It determines
the type of Table of Contents (ToC) structure (simple or nested/anchor-based)
and delegates the parsing task to the appropriate specialized parser module.
"""

import os
import traceback
from pathlib import Path
from typing import Dict, Any

from bs4 import BeautifulSoup
from ebooklib import epub

# Import các parser chuyên biệt
# Import các parser chuyên biệt
from .epub_parsers import anchor_based_parser, simple_toc_parser
# Import centralized utils
from .epub_parsers.utils import resolve_image_path, save_image_to_temp
from ..shared import debug_logger


def parse_epub(filepath: str) -> Dict[str, Any]:
    """
    Parses an EPUB file by dispatching to the correct specialized parser.

    Args:
        filepath: The path to the EPUB file.

    Returns:
        A dictionary containing the ebook's metadata and structured content.
    """
    results: Dict[str, Any] = {'metadata': {}, 'content': []}
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)

    try:
        debug_logger.log(f"Bắt đầu phân tích EPUB: {filepath}")
        book = epub.read_epub(filepath)

        # --- Trích xuất Metadata & Ảnh bìa ---
        try:
            results['metadata']['title'] = book.get_metadata('DC', 'title')[0][0]
        except (IndexError, TypeError):
            results['metadata']['title'] = Path(filepath).stem
        try:
            results['metadata']['author'] = book.get_metadata('DC', 'creator')[0][0]
        except (IndexError, TypeError):
            results['metadata']['author'] = 'Không rõ'

        cover_path = ""
        cover_id = None
        
        # 1. Try to find cover ID from metadata (standard OPF way)
        try:
            # Debug metadata structure to understand namespace issues
            debug_logger.log(f"Metadata namespaces: {list(book.metadata.keys())}")
            
            opf_ns = 'http://www.idpf.org/2007/opf'
            if opf_ns in book.metadata and 'meta' in book.metadata[opf_ns]:
                for meta_val, meta_attrs in book.metadata[opf_ns]['meta']:
                    if meta_attrs.get('name') == 'cover':
                        cover_id = meta_attrs.get('content')
                        debug_logger.log(f"Found cover ID from metadata: {cover_id}")
                        break
        except Exception as e:
            debug_logger.log(f"Error reading metadata for cover: {e}")

        cover_item = book.get_item_with_id(cover_id) if cover_id else None

        # 2. Fallback: Try standard IDs
        if not cover_item:
            for potential_id in ['cover', 'cover-image', 'coverimage']:
                 cover_item = book.get_item_with_id(potential_id)
                 if cover_item:
                     debug_logger.log(f"Found cover via fallback ID: {potential_id}")
                     break
        
        # 3. Fallback: Try filenames (startswith/endswith)
        if not cover_item:
            for item in book.get_items():
                name = item.get_name().lower()
                if 'cover' in name and (
                    name.endswith('.xhtml') or 
                    name.endswith('.html') or 
                    name.endswith('.jpg') or 
                    name.endswith('.jpeg')
                ):
                    # Prioritize exact matches or "cover" at end of name
                    if name.endswith('cover.xhtml') or name.endswith('cover.html') or 'cover' in name.split('/')[-1]:
                        cover_item = item
                        debug_logger.log(f"Found cover via filename: {name}")
                        break
        
        if cover_item:
            try:
                # Check if the cover item is an image itself
                media_type = getattr(cover_item, 'media_type', '').lower()
                file_name = cover_item.get_name().lower()
                
                debug_logger.log(f"Inspecting cover item: id={cover_item.get_id()}, name={file_name}, media_type={media_type}")

                is_direct_image = (
                    media_type.startswith('image/') or 
                    file_name.endswith(('.jpg', '.jpeg', '.png', '.gif'))
                )

                if is_direct_image:
                    debug_logger.log(f"Cover item is a direct image: {file_name}")
                    cover_path = save_image_to_temp(
                        cover_item, temp_image_dir, "epub_cover_"
                    )
                else:
                    debug_logger.log("Cover item is considered HTML wrapper. Parsing with BeautifulSoup.")
                    # Assume it's an HTML/XHTML wrapper
                    soup = BeautifulSoup(cover_item.get_content(), 'xml')
                    img_tag = soup.find('img')
                    if img_tag and img_tag.get('src'):
                        final_cover_item = resolve_image_path(img_tag.get('src'), cover_item, book)
                        if final_cover_item:
                            cover_path = save_image_to_temp(
                                final_cover_item, temp_image_dir, "epub_cover_"
                            )
                        else:
                            debug_logger.log(f"Could not resolve image path from src: {img_tag.get('src')}")
                    else:
                         debug_logger.log("No img tag found in cover wrapper.")
            except Exception as e:  # pylint: disable=broad-except
                debug_logger.log(f"Error processing cover item: {e}")
                pass
        else:
            debug_logger.log("No cover item found after all fallback attempts.")
        results['metadata']['cover_image_path'] = cover_path

        # --- Logic Điều phối ---
        is_nested = any(isinstance(item, (list, tuple)) for item in book.toc)

        if is_nested:
            debug_logger.log("=> Detected nested ToC. Using anchor-based parser.")
            results['content'] = anchor_based_parser.parse(book, temp_image_dir)
        else:
            debug_logger.log("=> Detected simple ToC. Using simple ToC parser.")
            results['content'] = simple_toc_parser.parse(book, temp_image_dir)

        return results

    except Exception as e:
        traceback.print_exc()
        return {
            'metadata': {},
            'content': [{'title': 'Error', 'content': [('text', f"An error occurred: {e}")]}]
        }