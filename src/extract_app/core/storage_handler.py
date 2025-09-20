# file-path: src/extract_app/core/storage_handler.py
# version: 2.0
# last-updated: 2025-09-19
# description: Cải tiến logic sao chép file để đảm bảo lưu ảnh từ EPUB.

import shutil
from pathlib import Path
from typing import List, Dict, Any

def save_as_folders(structured_content: List[Dict[str, Any]], base_path: Path, book_name: str):
    """
    Lưu nội dung đã được cấu trúc hóa vào một cấu trúc thư mục.
    """
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
                    chapter_text_content.append(data)
                elif content_type == 'image':
                    # data là đường dẫn (string) tới file ảnh trong thư mục temp
                    image_source_path = Path(data)
                    
                    # --- LOGIC KIỂM TRA MỚI ---
                    if image_source_path.exists():
                        dest_filename = f"image_{image_counter:03d}{image_source_path.suffix}"
                        dest_path = chapter_dir / dest_filename
                        print(f"  Đang sao chép: {image_source_path} -> {dest_path}")
                        shutil.copy2(image_source_path, dest_path)
                        image_counter += 1
                    else:
                        print(f"  [Cảnh báo] Bỏ qua file ảnh không tồn tại: {image_source_path}")
            
            if chapter_text_content:
                with open(chapter_dir / "content.txt", "w", encoding="utf-8") as f:
                    f.write("\n\n".join(chapter_text_content))
        
        print(f"Lưu thành công vào: {book_dir}")
        return True, str(book_dir)
    except Exception as e:
        print(f"Lỗi khi lưu file: {e}")
        return False, str(e)