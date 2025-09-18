# file-path: src/extract_app/core/pdf_parser.py
# version: 2.1
# last-updated: 2025-09-17
# description: Thay đổi cấu trúc trả về thành danh sách các trang (list of lists).

import fitz  # PyMuPDF
from typing import List, Tuple, Any

def parse_pdf(filepath: str) -> List[List[Tuple[str, Any]]]:
    """
    Mở một file PDF và trích xuất nội dung, nhóm theo từng trang.

    Args:
        filepath: Đường dẫn đến file PDF.

    Returns:
        Một danh sách các danh sách. Mỗi danh sách con chứa content tuples của một trang.
        Ví dụ: [ [('text', 'page 1 text')], [('text', 'page 2 text'), ('image', b'...')] ]
    """
    all_pages_content = []
    try:
        doc = fitz.open(filepath)
        
        for page_num, page in enumerate(doc):
            single_page_content = []
            
            # Thêm khối văn bản
            page_text = page.get_text("text")
            if page_text.strip():
                single_page_content.append(('text', page_text))

            # Thêm các khối hình ảnh
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                single_page_content.append(('image', image_bytes))
            
            if single_page_content:
                all_pages_content.append(single_page_content)
        
        doc.close()
        return all_pages_content
    except Exception as e:
        print(f"Lỗi khi xử lý file PDF: {e}")
        return [[('text', f"Không thể đọc file: {filepath}. Lỗi: {e}")]]