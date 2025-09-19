# file-path: src/extract_app/core/storage_handler.py
# version: 1.1
# last-updated: 2025-09-19
# description: Sửa lỗi không lưu được hình ảnh từ file EPUB.

import shutil
from pathlib import Path
from typing import List, Dict, Any

def save_as_folders(structured_content: List[Dict[str, Any]], base_path: Path, book_name: str):
    """
    Lưu nội dung đã được cấu trúc hóa vào một cấu trúc thư mục.

    Args:
        structured_content: Dữ liệu đã được parser xử lý.
        base_path: Thư mục do người dùng chọn để lưu.
        book_name: Tên sách (dùng để tạo thư mục gốc).
    """
    try:
        book_dir = base_path / Path(book_name).stem
        book_dir.mkdir(exist_ok=True)

        for i, section_data in enumerate(structured_content):
            title = section_data.get('title', f'Phan_{i+1}').strip()
            # Làm sạch tiêu đề để dùng làm tên thư mục
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-')]).rstrip()
            if not safe_title:  # Handle cases where the title becomes empty
                safe_title = f"Section {i+1}"
            chapter_dir = book_dir / f"{i+1:02d} - {safe_title}"
            chapter_dir.mkdir(exist_ok=True)

            chapter_text_content = []
            image_counter = 0

            for content_type, data in section_data.get('content', []):
                if content_type == 'text':
                    chapter_text_content.append(data)
                elif content_type == 'image':
                    # data là đường dẫn tới file ảnh trong thư mục temp
                    image_source_path = Path(data)
                    if image_source_path.exists():
                        # Sao chép ảnh từ temp vào thư mục chương
                        # Đổi tên file đích để tránh trùng lặp và dễ quản lý
                        dest_filename = f"image_{image_counter:03d}{image_source_path.suffix}"
                        dest_path = chapter_dir / dest_filename
                        shutil.copy2(image_source_path, dest_path)
                        image_counter += 1
            
            # Ghi toàn bộ text của chương vào một file duy nhất
            if chapter_text_content:
                with open(chapter_dir / "content.txt", "w", encoding="utf-8") as f:
                    f.write("\n\n".join(chapter_text_content))
        
        print(f"Lưu thành công vào: {book_dir}")
        return True, str(book_dir)
    except Exception as e:
        print(f"Lỗi khi lưu file: {e}")
        return False, str(e)