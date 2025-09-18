# file-path: src/extract_app/core/pdf_parser.py
# version: 4.1
# last-updated: 2025-09-18
# description: Lưu ảnh ra thư mục tạm và trả về đường dẫn (anchor) thay vì data bytes.

import fitz
from typing import List, Dict, Any
from pathlib import Path

def parse_pdf(filepath: str) -> List[Dict[str, Any]]:
    structured_content = []
    
    # Tạo thư mục tạm để lưu ảnh
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(filepath)
        toc = doc.get_toc()

        if not toc:
            # ... (logic fallback không đổi)
            return [{'title': 'Lỗi', 'content': [('text', 'File PDF này không chứa Mục lục.')]}]

        toc.sort(key=lambda item: item[2])

        for i, item in enumerate(toc):
            level, title, start_page = item
            start_page -= 1 
            end_page = doc.page_count
            if i + 1 < len(toc):
                end_page = toc[i+1][2] - 1
            
            chapter_content = []
            for page_num in range(start_page, end_page):
                page = doc.load_page(page_num)
                
                # Logic lấy text không đổi
                page_text = page.get_text("text")
                if page_text.strip():
                    chapter_content.append(('text', page_text))

                # Logic lấy ảnh được CẬP NHẬT
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Lưu ảnh ra file tạm
                    image_filename = f"img_p{page_num+1}_i{img_index}.{image_ext}"
                    image_path = temp_image_dir / image_filename
                    with open(image_path, "wb") as f_image:
                        f_image.write(image_bytes)
                    
                    # Trả về đường dẫn (anchor) thay vì dữ liệu bytes
                    chapter_content.append(('image', str(image_path)))
            
            if chapter_content:
                structured_content.append({'title': title, 'content': chapter_content})

        doc.close()
        return structured_content
    except Exception as e:
        print(f"Lỗi khi xử lý file PDF: {e}")
        return [{'title': 'Lỗi', 'content': [('text', f"Lỗi: {e}")]}]