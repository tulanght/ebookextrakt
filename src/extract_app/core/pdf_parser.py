# file-path: src/extract_app/core/pdf_parser.py
# version: 7.1 (Pylint Compliance)
# last-updated: 2025-09-26
# description: Cleans up the PDF parser module to meet Pylint standards.

"""
PDF Parser Module.

This module is responsible for extracting content (metadata, text, and images)
from PDF files. It uses a multi-tiered approach to determine the document's
structure, trying bookmarks first, then a text-based heuristic, and finally
falling back to per-page splitting.
"""

import re
import traceback
from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF


def _parse_toc_from_text(doc: fitz.Document) -> List:
    """
    Tries to heuristically parse a Table of Contents from the text of the
    first few pages of the document.
    """
    print("Đang thử phân tích Mục lục từ text...")
    toc = []
    # Pattern to find lines like "Chapter 1 .......... 5"
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
                # Avoid matching random lines by checking title length
                if len(title) > 3:
                    page_number = int(match.group(2))
                    toc.append([1, title, page_number])

    if toc:
        print(f"  -> Heuristic đã tìm thấy {len(toc)} mục từ text.")
    else:
        print("  -> Heuristic không tìm thấy mục lục nào từ text.")
    return toc


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def parse_pdf(filepath: str) -> Dict[str, Any]:
    """
    Parses a PDF file and extracts its structure, metadata, and content.

    Args:
        filepath: The path to the PDF file.

    Returns:
        A dictionary containing the PDF's metadata and structured content.
    """
    results: Dict[str, Any] = {'metadata': {}, 'content': []}
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc: fitz.Document = fitz.open(filepath)

        meta = doc.metadata
        results['metadata']['title'] = meta.get('title', Path(filepath).stem)
        results['metadata']['author'] = meta.get('author', 'Không rõ')

        # Extract cover image from the first page
        cover_path = ""
        if doc.page_count > 0:
            first_page_images = doc.load_page(0).get_images(full=True)
            if first_page_images:
                img_info = first_page_images[0]
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    cover_filename = f"pdf_cover.{image_ext}"
                    image_path = temp_image_dir / cover_filename
                    with open(image_path, "wb") as f_image:
                        f_image.write(image_bytes)
                    cover_path = str(image_path)
        results['metadata']['cover_image_path'] = cover_path

        # Determine Table of Contents source
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
            _, title, start_page = item
            start_page = max(start_page - 1, 0)

            end_page = doc.page_count
            if i + 1 < len(toc):
                next_start_page = toc[i+1][2] - 1
                end_page = next_start_page if next_start_page > start_page else start_page + 1

            chapter_content = []
            for page_num in range(start_page, end_page):
                if page_num >= doc.page_count:
                    continue
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                if page_text.strip():
                    chapter_content.append(('text', page_text))

                for img_index, img in enumerate(page.get_images(full=True)):
                    img_xref = img[0]
                    img_base = doc.extract_image(img_xref)
                    if img_base:
                        img_bytes = img_base["image"]
                        img_ext = img_base["ext"]
                        img_filename = f"pdf_p{page_num+1}_i{img_index}.{img_ext}"
                        img_path = temp_image_dir / img_filename
                        with open(img_path, "wb") as f_img:
                            f_img.write(img_bytes)
                        img_data = {'anchor': str(img_path), 'caption': ''}
                        chapter_content.append(('image', img_data))

            if chapter_content:
                node = {'title': title, 'content': chapter_content, 'children': []}
                content_tree.append(node)

        results['content'] = content_tree
        doc.close()
        return results

    except Exception:
        traceback.print_exc()
        return {'metadata': {}, 'content': []}