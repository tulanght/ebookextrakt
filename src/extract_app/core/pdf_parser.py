# file-path: src/extract_app/core/pdf_parser.py (HOÀN CHỈNH)
# version: 7.0
# last-updated: 2025-09-23
# description: Refactored to return a tree structure consistent with epub_parser.

import fitz
import re
from typing import List, Dict, Any
from pathlib import Path

def _parse_toc_from_text(doc) -> List:
    print("Đang thử phân tích Mục lục từ text...")
    toc = []
    toc_pattern = re.compile(r'(.+?)\s*[.\s]{3,}\s*(\d+)')
    
    scan_pages = min(20, doc.page_count)
    for page_num in range(scan_pages):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        lines = text.split('\n')
        for line in lines:
            match = toc_pattern.match(line.strip())
            if match:
                title = match.group(1).strip()
                if len(title) > 3: # Avoid matching random lines
                    page_number = int(match.group(2))
                    toc.append([1, title, page_number])
    
    if toc: print(f"  -> Heuristic đã tìm thấy {len(toc)} mục từ text.")
    else: print("  -> Heuristic không tìm thấy mục lục nào từ text.")
    return toc

def parse_pdf(filepath: str) -> Dict[str, Any]:
    results = {'metadata': {}, 'content': []}
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        doc = fitz.open(filepath)
        
        meta = doc.metadata
        results['metadata']['title'] = meta.get('title', Path(filepath).stem)
        results['metadata']['author'] = meta.get('author', 'Không rõ')
        cover_path = ""
        if doc.page_count > 0:
            first_page_images = doc.load_page(0).get_images(full=True)
            if first_page_images:
                img_info = first_page_images[0]; xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]; image_ext = base_image["ext"]
                cover_filename = f"pdf_cover.{image_ext}"
                image_path = temp_image_dir / cover_filename
                with open(image_path, "wb") as f_image: f_image.write(image_bytes)
                cover_path = str(image_path)
        results['metadata']['cover_image_path'] = cover_path

        toc = doc.get_toc()
        source = "Bookmarks"
        if not toc:
            toc = _parse_toc_from_text(doc)
            source = "Text Heuristic"
        if not toc:
            print("Không tìm thấy Mục lục, sẽ chia theo từng trang.")
            source = "Per-Page Splitting"
            toc = [[1, f"Trang {i+1}", i+1] for i in range(doc.page_count)]
        print(f"Đã xác định cấu trúc bằng phương pháp: {source}")
        
        content_tree = []
        toc.sort(key=lambda item: item[2])
        for i, item in enumerate(toc):
            level, title, start_page = item
            start_page -= 1
            if start_page < 0: start_page = 0
            
            end_page = doc.page_count
            if i + 1 < len(toc):
                next_start_page = toc[i+1][2] - 1
                end_page = next_start_page if next_start_page > start_page else start_page + 1

            chapter_content = []
            for page_num in range(start_page, end_page):
                if page_num >= doc.page_count: continue
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                if page_text.strip(): chapter_content.append(('text', page_text))
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]; image_ext = base_image["ext"]
                    image_filename = f"pdf_p{page_num+1}_i{img_index}.{image_ext}"
                    image_path = temp_image_dir / image_filename
                    with open(image_path, "wb") as f_image: f_image.write(image_bytes)
                    image_data = {'anchor': str(image_path), 'caption': ''}
                    chapter_content.append(('image', image_data))
            
            if chapter_content:
                node = {'title': title, 'content': chapter_content, 'children': [] }
                content_tree.append(node)
        
        results['content'] = content_tree
        doc.close()
        return results
        
    except Exception as e:
        import traceback; traceback.print_exc()
        return {'metadata': {}, 'content': []}