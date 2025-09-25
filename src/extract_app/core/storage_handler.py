# file-path: src/extract_app/core/storage_handler.py
# version: 5.0
# last-updated: 2025-09-25
# description: Inserts formatted Image Anchors with captions into content.txt files.

import shutil
from pathlib import Path
from typing import List, Dict, Any

def _save_node_recursively(node: Dict[str, Any], parent_path: Path, level: int, index: int):
    """
    Đệ quy lưu một node và các con của nó, tạo ra các thư mục lồng nhau.
    """
    title = node.get('title', f'Section_{index+1}').strip()
    safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-')]).rstrip()
    if not safe_title: safe_title = f"Untitled_{index+1}"
    
    current_path = parent_path / f"{index+1:02d} - {safe_title}"
    current_path.mkdir(exist_ok=True)

    content_list = node.get('content', [])
    if content_list:
        # --- LOGIC GHI FILE ĐÃ CẬP NHẬT ---
        full_text_content = []
        image_counter = 0
        for content_type, data in content_list:
            if content_type == 'text':
                # Đảm bảo dữ liệu text là string
                if isinstance(data, dict): # Xử lý trường hợp từ PDF parser
                    full_text_content.append(data.get('content', ''))
                else:
                    full_text_content.append(str(data))

            elif content_type == 'image' and isinstance(data, dict):
                anchor_path_str = data.get('anchor', '')
                if not anchor_path_str: continue

                anchor_path = Path(anchor_path_str)
                if anchor_path.exists():
                    # Sao chép file ảnh
                    dest_filename = f"image_{image_counter:03d}{anchor_path.suffix}"
                    dest_path = current_path / dest_filename
                    shutil.copy2(anchor_path, dest_path)
                    image_counter += 1

                    # Tạo thẻ Image Anchor
                    caption = data.get('caption', '').strip()
                    anchor_tag = f"[Image Anchor: {dest_filename}"
                    if caption:
                        anchor_tag += f" - Caption: {caption}"
                    anchor_tag += "]"
                    full_text_content.append(anchor_tag)
        
        if full_text_content:
            with open(current_path / "content.txt", "w", encoding="utf-8") as f:
                f.write("\n\n".join(full_text_content))

    # Đệ quy lưu các con
    children = node.get('children', [])
    for i, child_node in enumerate(children):
        _save_node_recursively(child_node, current_path, level + 1, i)


def save_as_folders(structured_content: List[Dict[str, Any]], base_path: Path, book_name: str):
    try:
        book_dir = base_path / Path(book_name).stem
        book_dir.mkdir(exist_ok=True)

        for i, root_node in enumerate(structured_content):
            _save_node_recursively(root_node, book_dir, 0, i)
        
        return True, str(book_dir)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)