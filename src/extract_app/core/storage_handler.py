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

def save_as_folders(
    structured_content: List[Dict[str, Any]], 
    base_path: Path, 
    book_name: str,
    progress_callback: Any = None
) -> tuple[bool, str]:
    """
    Saves the structured content with optional progress reporting.
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

                    percent = processed_nodes / total_nodes
                    title = node.get('title', 'Untitled')
                    progress_callback(percent, f"Saving: {title[:20]}...")

                _save_node_recursively(node, parent, i)

        # Modify _save_node_recursively to NOT recurse itself, but we need it to recuse?
        # Actually modifying _save_node_recursively signature is cleaner.
        # But to avoid massive diff, let's inject a wrapper or modify the existing function.
        # Modifying existing function is better for recursion.
        
        # Redefining strategy: 
        # We will use a mutable context to track progress across the existing recursive function.
        
        context = {'processed': 0, 'total': total_nodes}
        
        def _save_with_progress(node, parent, index):
             # 1. Save this node
             _save_node_recursively(node, parent, index)
             
             # 2. Update Progress
             context['processed'] += 1
             if progress_callback and context['total'] > 0:
                 percent = context['processed'] / context['total']
                 title = node.get('title', 'Untitled')
                 progress_callback(percent, f"Saving: {title[:30]}...")

        # We actually need to modify _save_node_recursively to let us hook in, 
        # OR we just copy the logic. 
        # Or, we Monkey Patch? No.
        # Let's just refactor _save_node_recursively to accept a callback too?
        # A simpler way: Iterate the tree slightly differently or just pass the callback down.
        # Let's Rewrite _save_node_recursively to accept context.
        pass
        
        # REAL IMPLEMENTATION START
        # Since I cannot easily change _save_node_recursively in this Replace block without changing the whole file,
        # I will augment _save_node_recursively to take an optional 'on_save_complete' callback?
        # No, simpler: I will fully replace _save_node_recursively in the file since it is small enough.
        
        # See next Tool Call for full file replace or significant chunk replace.
        raise NotImplementedError("Use MultiReplace for this complex change")

    except Exception as e:
        traceback.print_exc()
        return False, str(e)