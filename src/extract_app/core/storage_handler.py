# file-path: src/extract_app/core/storage_handler.py (HOÀN CHỈNH)
# version: 3.1
# last-updated: 2025-09-22
# description: Hotfix - Sửa lỗi TypeError khi lưu kết quả từ PDF đã qua xử lý.

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

            chapter_text_content = []
            image_counter = 0

            for content_type, data in section_data.get('content', []):
                if content_type == 'text':
                    # --- SỬA LỖI TẠI ĐÂY ---
                    # Kiểm tra nếu data là dict, lấy key 'content'.
                    # Ngược lại (từ EPUB), nó là string, dùng trực tiếp.
                    if isinstance(data, dict):
                        chapter_text_content.append(data.get('content', ''))
                    elif isinstance(data, str):
                        chapter_text_content.append(data)
                
                elif content_type == 'image':
                    anchor_path_str = data.get('anchor', '') if isinstance(data, dict) else data
                    image_source_path = Path(anchor_path_str)
                    
                    if image_source_path.exists():
                        dest_filename = f"image_{image_counter:03d}{image_source_path.suffix}"
                        dest_path = chapter_dir / dest_filename
                        shutil.copy2(image_source_path, dest_path)
                        image_counter += 1
            
            if chapter_text_content:
                with open(chapter_dir / "content.txt", "w", encoding="utf-8") as f:
                    f.write("\n\n".join(chapter_text_content))
        
        print(f"Lưu thành công vào: {book_dir}")
        return True, str(book_dir)
    except Exception as e:
        print(f"Lỗi khi lưu file: {e}")
        return False, str(e)