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


def _save_node_recursively(node: Dict[str, Any], parent_path: Path, index: int):
    """
    Recursively saves a content node and its children, creating a nested
    directory structure that mirrors the ebook's table of contents.
    """
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
                    # Copy the image file
                    dest_filename = f"image_{image_counter:03d}{anchor_path.suffix}"
                    shutil.copy2(anchor_path, current_path / dest_filename)
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
        _save_node_recursively(child_node, current_path, i)


def save_as_folders(
    structured_content: List[Dict[str, Any]], base_path: Path, book_name: str
) -> tuple[bool, str]:
    """
    Saves the structured content as a directory of folders and files.

    Args:
        structured_content: The hierarchical content tree.
        base_path: The root directory to save into.
        book_name: The name of the book, used for the main folder.

    Returns:
        A tuple containing a success flag and the path to the saved directory or an error message.
    """
    try:
        book_dir = base_path / Path(book_name).stem
        book_dir.mkdir(exist_ok=True)

        for i, root_node in enumerate(structured_content):
            _save_node_recursively(root_node, book_dir, i)

        return True, str(book_dir)
    except Exception as e:
        traceback.print_exc()
        return False, str(e)