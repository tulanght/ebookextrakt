# file-path: src/extract_app/core/pdf_parser.py
# version: 2.0
# last-updated: 2025-09-17
# description: Nâng cấp để trích xuất cả văn bản và hình ảnh từ file PDF.

import fitz  # PyMuPDF
from typing import List, Tuple, Any

def parse_pdf(filepath: str) -> List[Tuple[str, Any]]:
    """
    Mở một file PDF và trích xuất nội dung dưới dạng danh sách các khối văn bản và hình ảnh.

    Args:
        filepath: Đường dẫn đến file PDF.

    Returns:
        Một danh sách các tuple, mỗi tuple chứa ('loại_nội_dung', dữ_liệu).
        Ví dụ: [('text', 'Đây là văn bản.'), ('image', b'...dữ liệu bytes của ảnh...')]
    """
    content_list = []
    try:
        doc = fitz.open(filepath)
        
        for page_num, page in enumerate(doc):
            # Thêm khối văn bản
            page_text = page.get_text("text")
            if page_text.strip():
                content_list.append(('text', page_text))

            # Thêm các khối hình ảnh
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                content_list.append(('image', image_bytes))
        
        doc.close()
        return content_list
    except Exception as e:
        print(f"Lỗi khi xử lý file PDF: {e}")
        content_list.append(('text', f"Không thể đọc file: {filepath}. Lỗi: {e}"))
        return content_list