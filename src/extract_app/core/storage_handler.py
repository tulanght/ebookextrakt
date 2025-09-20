# file-path: src/extract_app/core/storage_handler.py
# version: 3.0
# last-updated: 2025-09-20
# description: Chèn image anchor và caption vào đúng vị trí trong file content.txt..

import shutil
from pathlib import Path
from typing import List, Dict, Any

def save_as_folders(structured_content: List[Dict[str, Any]], base_path: Path, book_name: str):
    try:
        book_dir = base_path / Path(book_name).stem
        book_dir.mkdir(exist_ok=True)
        print(f"Đã tạo/xác nhận thư mục sách: {book_dir}")

        for i, section_data in enumerate(structured_content):
            title = section_data.get('title', f'Phan_{i+1}').strip()
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-')]).rstrip()
            if not safe_title: safe_title = f"Section_{i+1}"
            
            chapter_dir = book_dir / f"{i+1:02d} - {safe_title}"
            chapter_dir.mkdir(exist_ok=True)

            image_counter = 0

            # --- LOGIC GHI FILE MỚI ---
            with open(chapter_dir / "content.txt", "w", encoding="utf-8") as f:
                for content_type, data in section_data.get('content', []):
                    if content_type == 'text':
                        f.write(data + "\n\n")
                    
                    elif content_type == 'image':
                        # Data bây giờ là một dictionary {'anchor': ..., 'caption': ...}
                        anchor_path_str = data.get('anchor', '')
                        caption = data.get('caption', '')
                        
                        image_source_path = Path(anchor_path_str)
                        if image_source_path.exists():
                            # Sao chép ảnh
                            dest_filename = f"image_{image_counter:03d}{image_source_path.suffix}"
                            dest_path = chapter_dir / dest_filename
                            shutil.copy2(image_source_path, dest_path)
                            
                            # Ghi anchor và caption vào file text
                            anchor_line = f"[IMAGE: {dest_filename}"
                            if caption:
                                anchor_line += f" | CAPTION: {caption}"
                            anchor_line += "]\n\n"
                            f.write(anchor_line)
                            
                            image_counter += 1
        
        print(f"Lưu thành công vào: {book_dir}")
        return True, str(book_dir)
    except Exception as e:
        print(f"Lỗi khi lưu file: {e}")
        return False, str(e)