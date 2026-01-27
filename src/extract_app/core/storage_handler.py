# file-path: src/extract_app/core/storage_handler.py
# version: 5.1 (Pylint Compliance)
# last-updated: 2025-09-26
# description: Cleans up the storage handler module to meet Pylint standards.

"""
Storage Handler Module.

This module is responsible for saving the structured content extracted from
ebooks into a nested folder structure on the local filesystem.
"""

import shutil
import traceback
from pathlib import Path
from typing import List, Dict, Any


def _save_node_recursively(node: Dict[str, Any], parent_path: Path, index: int, progress_ctx: Dict = None):
    """
    Recursively saves a content node and its children.
    """
    # 0. Update Progress (Pre-save or Post-save? Pre-save to show "Saving X")
    if progress_ctx:
        progress_ctx['processed'] += 1
        if progress_ctx['callback'] and progress_ctx['total'] > 0:
             percent = progress_ctx['processed'] / progress_ctx['total']
             title = node.get('title', 'Untitled')
             # Throttle updates? No, UI handles it or we can check time.
             progress_ctx['callback'](percent, f"Saving: {title[:30]}...")

    title = node.get('title', f'Section_{index+1}').strip()
    # Sanitize the title to create a valid directory name
    safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-')]).rstrip()
    if not safe_title:
        safe_title = f"Untitled_{index+1}"

    current_path = parent_path / f"{index+1:02d} - {safe_title}"
    current_path.mkdir(exist_ok=True)

    content_list = node.get('content', [])
    if content_list:
        full_text_content = []
        image_counter = 0
        seen_images = {}  # Map source_anchor_path -> dest_filename

        for content_type, data in content_list:
            if content_type == 'text':
                # Ensure text data is a string
                if isinstance(data, dict):  # Handle dicts from PDF parser
                    full_text_content.append(data.get('content', ''))
                else:
                    full_text_content.append(str(data))

            elif content_type == 'image' and isinstance(data, dict):
                anchor_path_str = data.get('anchor', '')
                if not anchor_path_str:
                    continue

                anchor_path = Path(anchor_path_str)
                if anchor_path.exists():
                    # Check if we've already saved this image in this folder
                    if anchor_path_str in seen_images:
                        dest_filename = seen_images[anchor_path_str]
                    else:
                        # Copy the image file
                        dest_filename = f"image_{image_counter:03d}{anchor_path.suffix}"
                        shutil.copy2(anchor_path, current_path / dest_filename)
                        seen_images[anchor_path_str] = dest_filename
                        image_counter += 1

                    # Create a formatted Image Anchor tag
                    caption = data.get('caption', '').strip()
                    anchor_tag = f"[Image Anchor: {dest_filename}"
                    if caption:
                        anchor_tag += f" - Caption: {caption}"
                    anchor_tag += "]"
                    full_text_content.append(anchor_tag)

        if full_text_content:
            with open(current_path / "content.txt", "w", encoding="utf-8") as f:
                f.write("\n\n".join(full_text_content))

    # Recursively save children nodes
    children = node.get('children', [])
    for i, child_node in enumerate(children):
        _save_node_recursively(child_node, current_path, i, progress_ctx)


def _count_total_nodes(nodes: List[Dict[str, Any]]) -> int:
    """Helper to count total nodes for progress tracking."""
    count = 0
    for node in nodes:
        count += 1
        count += _count_total_nodes(node.get('children', []))
    return count

def _save_db_recursively(node: Dict[str, Any], db_manager: Any, chapter_id: int, order_index: int):
    """
    Recursively saves a node as an Article in the database.
    """
    subtitle = node.get('title', 'Untitled')
    content_list = node.get('content', [])
    
    # Construct text content
    full_text = []
    
    # We also need to save images to the images table so we need to know the article_id first
    # But we haven't created it yet.
    
    # Extract text first
    for content_type, data in content_list:
        if content_type == 'text':
             if isinstance(data, dict):
                 full_text.append(data.get('content', ''))
             else:
                 full_text.append(str(data))
        elif content_type == 'image':
             # Placeholder for image in text
             anchor = data.get('anchor', '')
             if anchor:
                 full_text.append(f"[Image: {Path(anchor).name}]")

    text_content = "\n\n".join(full_text)
    
    # Create Article
    article_id = db_manager.add_article(chapter_id, subtitle, text_content, order_index)
    
    # Save Images
    for content_type, data in content_list:
        if content_type == 'image' and isinstance(data, dict):
             anchor = data.get('anchor', '')
             caption = data.get('caption', '')
             if anchor:
                 db_manager.add_image(article_id, anchor, caption)
                 
    # Recurse for children (Flattening: Children become subsequential articles of the SAME chapter?
    # Or do we treat them as part of this article? 
    # Current DB schema (Chapter -> Article) implies 2 levels. 
    # Logic: If I am a child of a Chapter, I am an Article. 
    # If I am a child of an Article... I am just another Article in the same Chapter, maybe with a prefix?
    # Let's just add them to the same Chapter for now to keep it simple.)
    
    children = node.get('children', [])
    for i, child_node in enumerate(children):
        # Continue adding to the SAME chapter, effectively flattening the tree under that chapter
        _save_db_recursively(child_node, db_manager, chapter_id, order_index + 1000 + i) 


def save_as_folders(
    structured_content: List[Dict[str, Any]], 
    base_path: Path, 
    book_name: str,
    progress_callback: Any = None,
    db_manager: Any = None,
    author: str = "Unknown",
    original_path: str = ""
) -> tuple[bool, str]:
    """
    Saves the structured content with optional progress reporting and DB integration.
    """
    try:
        book_dir = base_path / Path(book_name).stem
        book_dir.mkdir(exist_ok=True)
        
        # Setup progress context
        progress_ctx = None
        if progress_callback:
            total = _count_total_nodes(structured_content)
            progress_ctx = {
                'total': total,
                'processed': 0,
                'callback': progress_callback
            }
            progress_callback(0.0, "Starting save...")

        # 1. DB: Create Book
        book_id = -1
        if db_manager:
            # Check for cover in content? Or metadata? (passed via args?) 
            # MainWindow keeps metadata in current_results but we passed only author.
            # Let's try to find cover from content if possible, or just ignore for now.
            cover_path = "" # Todo: pass cover path
            book_id = db_manager.add_book(book_name, author, original_path, cover_path)

        for i, root_node in enumerate(structured_content):
            # File System Save
            _save_node_recursively(root_node, book_dir, i, progress_ctx)
            
            # DB Save (Top level nodes become Chapters)
            if db_manager and book_id != -1:
                title = root_node.get('title', f"Chapter {i+1}")
                chapter_id = db_manager.add_chapter(book_id, title, i)
                
                # Check if root node ITSELF has content (it might be an article too)
                if root_node.get('content'):
                    _save_db_recursively(root_node, db_manager, chapter_id, 0)
                
                # Recurse children as Articles of this Chapter
                for j, child in enumerate(root_node.get('children', [])):
                     _save_db_recursively(child, db_manager, chapter_id, j+1)

        return True, str(book_dir)
             


    except Exception as e:
        traceback.print_exc()
        return False, str(e)