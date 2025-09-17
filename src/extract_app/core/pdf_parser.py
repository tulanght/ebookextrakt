# file-path: src/extract_app/core/pdf_parser.py
# version: 1.0
# last-updated: 2025-09-17
# description: Chứa logic nghiệp vụ để trích xuất nội dung từ file PDF.

import fitz  # PyMuPDF

def extract_text_from_pdf(filepath: str) -> str:
    """
    Mở một file PDF và trích xuất toàn bộ nội dung văn bản từ các trang.

    Args:
        filepath: Đường dẫn đến file PDF.

    Returns:
        Một chuỗi chứa toàn bộ văn bản đã được trích xuất.
    """
    try:
        doc = fitz.open(filepath)
        full_text = []
        for page in doc:
            full_text.append(page.get_text())
        
        doc.close()
        return "".join(full_text)
    except Exception as e:
        print(f"Lỗi khi xử lý file PDF: {e}")
        return f"Không thể đọc file: {filepath}. Lỗi: {e}"