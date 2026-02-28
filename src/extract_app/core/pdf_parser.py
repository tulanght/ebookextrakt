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
import statistics
import traceback
from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF
from ..shared import debug_logger


def _parse_toc_from_text(doc: fitz.Document) -> List:
    """
    Tries to heuristically parse a Table of Contents from the text of the
    first few pages of the document.
    """
    debug_logger.log("Đang thử phân tích Mục lục từ text...")
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
        debug_logger.log(f"  -> Heuristic đã tìm thấy {len(toc)} mục từ text.")
    else:
        debug_logger.log("  -> Heuristic không tìm thấy mục lục nào từ text.")
    return toc


# pylint: disable=too-many-locals, too-many-branches

# Chapters matching these patterns are extracted as a single flat article (no splitting).
_SKIP_SPLIT_PATTERNS = [
    'INDEX', 'GLOSSARY', 'REFERENCES', 'BIBLIOGRAPHY',
    'CONTENTS', 'TABLE OF CONTENTS', 'APPENDIX', 'APPENDICES',
    'ENDNOTES', 'FOOTNOTES', 'COPYRIGHT', 'COLOPHON',
    'ABOUT THE AUTHOR', 'ACKNOWLEDGMENT', 'ABOUT THIS'
]

def _extract_flat_chapter(doc, start_page, end_page, chapter_title, temp_image_dir):
    """Extracts pages as a single flat article — no heading splitting.
    Used for utility sections like INDEX, GLOSSARY, REFERENCES."""
    content = []
    for page_num in range(start_page, end_page):
        if page_num >= doc.page_count:
            continue
        page = doc.load_page(page_num)
        text = page.get_text("text").strip()
        if text:
            content.append(('text', text + "\n"))
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
                content.append(('image', {'anchor': str(img_path), 'caption': ''}))
    return [{'title': chapter_title, 'content': content, 'children': []}]

def _extract_chapter_with_heuristics(doc, start_page, end_page, chapter_title, temp_image_dir, debug_logger=None):
    """Extracts pages and splits them into child articles based on font-size + bold heuristics.
    
    Strategy:
    - Pass 1: Scan all spans to find the median (body) font size.
    - Pass 2: Process line-by-line. A line is a "heading" if its first span is:
        (a) font size > median + 3pt (clearly larger), OR
        (b) font size > median AND uses a Bold font variant
      AND the line text is short (< 120 chars, single-line).
    - When a heading is detected, flush the current article and start a new one.
    """

    articles = []
    
    # Pass 1: Determine baseline (body) font size
    sizes = []
    for page_num in range(start_page, end_page):
        if page_num >= doc.page_count: continue
        page = doc.load_page(page_num)
        for b in page.get_text("dict")["blocks"]:
            if b["type"] == 0:
                for l in b["lines"]:
                    for s in l["spans"]:
                        text = s["text"].strip()
                        if text and len(text) > 3:
                            sizes.append(round(s["size"], 1))
                            
    baseline_size = statistics.median(sizes) if sizes else 11.0
    # Two thresholds:
    #   - "clearly larger" (e.g. 21pt vs 15pt body) → always a heading
    #   - "slightly larger + bold" (e.g. 16pt bold vs 15pt body) → heading if bold
    major_threshold = baseline_size + 3.0   # e.g. 15 + 3 = 18
    minor_threshold = baseline_size + 0.5   # e.g. 15 + 0.5 = 15.5

    if debug_logger:
        debug_logger.log(f"  [Heuristic] Baseline={baseline_size}pt, Major≥{major_threshold}pt, Minor≥{minor_threshold}pt+Bold")

    current_title = chapter_title
    current_content = []
    
    # Pass 2: Process blocks line-by-line
    for page_num in range(start_page, end_page):
        if page_num >= doc.page_count: continue
        page = doc.load_page(page_num)
        
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b["type"] == 0:
                for line in b["lines"]:
                    # Analyze the first non-empty span in this line
                    first_span = None
                    for s in line["spans"]:
                        if s["text"].strip():
                            first_span = s
                            break
                    if not first_span:
                        continue
                    
                    # Reconstruct line text
                    line_text = "".join(s["text"] for s in line["spans"]).strip()
                    if not line_text:
                        continue
                    
                    span_size = round(first_span["size"], 1)
                    font_name = first_span.get("font", "")
                    is_bold = "Bold" in font_name or "bold" in font_name or bool(first_span.get("flags", 0) & (1 << 4))
                    
                    # Heading detection
                    is_heading = False
                    if span_size >= major_threshold and len(line_text) < 120:
                        is_heading = True
                    elif span_size >= minor_threshold and is_bold and len(line_text) < 120:
                        # Bold + slightly larger → could be a sub-section heading
                        # But we only want to split on MAJOR headings (species names),
                        # not every bold sub-section like "TAXONOMY", "BEHAVIOR"
                        # So we require size to be significantly above baseline
                        if span_size >= baseline_size + 2.0:
                            is_heading = True
                    
                    if is_heading:
                        # Flush current article
                        if current_content:
                            articles.append({'title': current_title, 'content': current_content, 'children': []})
                        current_title = line_text
                        current_content = []
                    else:
                        current_content.append(('text', line_text + "\n"))

        # Process Images
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
                current_content.append(('image', img_data))

    if current_content or not articles:
        articles.append({'title': current_title, 'content': current_content, 'children': []})
        
    return articles

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
        debug_logger.log(f"Bắt đầu phân tích PDF: {filepath}")
        doc: fitz.Document = fitz.open(filepath)

        meta = doc.metadata
        
        # 1. Extract Title
        title = meta.get('title', '').strip()
        if not title:
            title = Path(filepath).stem
            
        # Clean title universally
        title = re.sub(r'\s*\(Z-Library\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'_(pdf|epub|mobi)$', '', title, flags=re.IGNORECASE)
        title = title.strip()
        
        # 2. Extract Author
        author = meta.get('author', 'Không rõ')
        
        # 3. Extract Year
        creation_date = meta.get('creationDate', '')
        published_year = ""
        # Format is usually D:YYYYMMDD...
        if creation_date.startswith('D:') and len(creation_date) >= 6:
            published_year = creation_date[2:6]
        else:
            # Fallback year from title/stem: e.g. "Some Book (2020)"
            year_match = re.search(r'\((\d{4})\)', title)
            if year_match:
                published_year = year_match.group(1)
                title = re.sub(r'\s*\(\d{4}\)', '', title).strip()
                
        results['metadata']['title'] = title
        results['metadata']['author'] = author
        results['metadata']['published_year'] = published_year

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
            debug_logger.log("Không tìm thấy Mục lục, sẽ chia theo từng trang.")
            source = "Per-Page Splitting"
            toc = [[1, f"Trang {i+1}", i+1] for i in range(doc.page_count)]
        debug_logger.log(f"Đã xác định cấu trúc bằng phương pháp: {source}")

        content_tree = []
        level_nodes = {}
        
        toc.sort(key=lambda item: item[2])
        for i, item in enumerate(toc):
            lvl, title, start_page = item
            debug_logger.log(f"Đang xử lý chương: {title} (Trang {start_page}, Cấp {lvl})")
            start_page = max(start_page - 1, 0)

            end_page = doc.page_count
            if i + 1 < len(toc):
                next_start_page = toc[i+1][2] - 1
                end_page = next_start_page if next_start_page > start_page else start_page + 1

            # Extract text and images with semantic splitting if applicable
            sub_articles = []
            
            # Skip splitting for utility/reference sections (see module-level constant)
            title_upper = title.strip().upper()
            should_skip_split = any(title_upper.startswith(pat) for pat in _SKIP_SPLIT_PATTERNS)
            
            if end_page > start_page:
                if should_skip_split:
                    debug_logger.log(f"  [Skip Split] Utility section detected: {title}")
                    sub_articles = _extract_flat_chapter(doc, start_page, end_page, title, temp_image_dir)
                else:
                    sub_articles = _extract_chapter_with_heuristics(doc, start_page, end_page, title, temp_image_dir, debug_logger)
            else:
                # Container node with no text
                sub_articles = [{'title': title, 'content': [], 'children': []}]

            if sub_articles:
                if len(sub_articles) == 1:
                    node = sub_articles[0]
                else:
                    # Treat the first article as chapter intro, rest as children
                    node = {'title': title, 'content': sub_articles[0]['content'], 'children': sub_articles[1:]}
                
                # Attach to parent based on hierarchy, or add as root
                if lvl == 1 or not level_nodes:
                    content_tree.append(node)
                else:
                    parent_lvl = lvl - 1
                    while parent_lvl > 0 and parent_lvl not in level_nodes:
                        parent_lvl -= 1
                    
                    if parent_lvl in level_nodes:
                        level_nodes[parent_lvl]['children'].append(node)
                    else:
                        content_tree.append(node)
                
                # Update tracker for this level
                level_nodes[lvl] = node

        results['content'] = content_tree
        doc.close()
        return results

    except Exception:
        traceback.print_exc()
        return {'metadata': {}, 'content': []}