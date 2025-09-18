# file-path: src/extract_app/core/pdf_parser.py
# version: 4.0
# last-updated: 2025-09-18
# description: Tái cấu trúc lớn để phân tích PDF dựa trên Mục lục (Bookmarks).

import fitz  # PyMuPDF
from typing import List, Dict, Any

def parse_pdf(filepath: str) -> List[Dict[str, Any]]:
    structured_content = []
    try:
        doc = fitz.open(filepath)
        toc = doc.get_toc()

        if not toc:
            print("Cảnh báo: File PDF không có Mục lục. Không thể phân tích theo chương.")
            return [{'title': 'Lỗi', 'content': [('text', 'File PDF này không chứa Mục lục (Bookmarks) để có thể phân tích theo chương.')]}]

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
                
                page_text = page.get_text("text")
                if page_text.strip():
                    chapter_content.append(('text', page_text))

                for img in page.get_images(full=True):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    chapter_content.append(('image', base_image["image"]))
            
            if chapter_content:
                structured_content.append({'title': title, 'content': chapter_content})

        doc.close()
        return structured_content
    except Exception as e:
        print(f"Lỗi khi xử lý file PDF: {e}")
        return [{'title': 'Lỗi', 'content': [('text', f"Lỗi: {e}")]}]