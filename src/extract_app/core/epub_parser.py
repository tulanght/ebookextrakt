# file-path: src/extract_app/core/epub_parser.py (HOÀN CHỈNH)
# version: 24.0
# last-updated: 2025-09-22
# description: Implements the final adaptive article splitting algorithm.

from ebooklib import epub
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any
from pathlib import Path
from collections import OrderedDict
import os

# ==============================================================================
# --- HELPER FUNCTIONS (Hàm hỗ trợ chung) ---
# ==============================================================================

def _flatten_toc_recursive(toc_items, flat_list):
    """Đệ quy làm phẳng cây ToC, xử lý mọi cấu trúc lồng nhau."""
    if isinstance(toc_items, epub.Link):
        flat_list.append(toc_items)
    elif hasattr(toc_items, '__iter__'):
        for item in toc_items:
            _flatten_toc_recursive(item, flat_list)

def _save_image_to_temp(image_item, temp_image_dir, prefix="epub_"):
    """Lưu file ảnh vào thư mục tạm và trả về anchor path."""
    image_bytes = image_item.get_content()
    image_filename = f"{prefix}{Path(image_item.get_name()).name}"
    image_path = temp_image_dir / image_filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    return str(image_path)

def _resolve_image_path(src, doc_item, book):
    """Giải quyết đường dẫn tương đối của ảnh."""
    if not src: return None
    current_dir = Path(doc_item.get_name()).parent
    resolved_path_str = os.path.normpath(os.path.join(current_dir, src)).replace('\\', '/')
    return book.get_item_with_href(resolved_path_str)

def _find_cover_from_toc(book, flat_toc):
    """Hàm hỗ trợ để tìm item ảnh bìa bằng cách quét các link trong ToC."""
    for link in flat_toc:
        if 'cover' in link.title.lower() or 'cover' in link.href.lower():
            cover_item = book.get_item_with_href(link.href)
            if cover_item:
                if cover_item.get_name().lower().endswith(('.xhtml', '.html')):
                    soup = BeautifulSoup(cover_item.get_content(), 'xml')
                    img_tag = soup.find('img')
                    if img_tag and img_tag.get('src'):
                        return _resolve_image_path(img_tag.get('src'), cover_item, book)
                else:
                    return cover_item
    return None

def _extract_html_content_sequentially(soup_body, book, doc_item, temp_image_dir) -> List:
    """Hàm chung để bóc tách text và image tuần tự từ một khối HTML."""
    content = []
    if not soup_body:
        return content

    content_tags = soup_body.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'div', 'img'])
    for tag in content_tags:
        for img_tag in tag.find_all('img'):
            src = img_tag.get('src')
            if not src: continue
            
            image_item = _resolve_image_path(src, doc_item, book)
            if image_item:
                anchor = _save_image_to_temp(image_item, temp_image_dir)
                caption = ""
                if img_tag.parent.name == 'figure':
                    caption_tag = img_tag.parent.find('figcaption')
                    if caption_tag:
                        caption = caption_tag.get_text(strip=True)
                content.append(('image', {'anchor': anchor, 'caption': caption}))
            img_tag.decompose()
        
        if tag.name != 'img':
            text = tag.get_text(strip=True)
            if text:
                content.append(('text', text))
    return content

# ==============================================================================
# --- STRATEGY A: TOC Traversal ---
# ==============================================================================
def _parse_by_toc_traversal(book, temp_image_dir) -> List[Dict[str, Any]]:
    structured_content = []
    flat_toc = []
    _flatten_toc_recursive(book.toc, flat_toc)
    
    for link in flat_toc:
        title = link.title
        href = link.href.split('#')[0]
        doc_item = book.get_item_with_href(href)
        if not doc_item: continue

        soup = BeautifulSoup(doc_item.get_content(), 'xml')
        chapter_content = _extract_html_content_sequentially(soup.body, book, doc_item, temp_image_dir)
        
        if chapter_content:
            structured_content.append({'title': title, 'content': chapter_content})
            
    return structured_content

# ==============================================================================
# --- STRATEGY B: Heuristic Scan ---
# ==============================================================================
def _get_unique_hrefs_from_toc(toc_items, unique_hrefs):
    """Đệ quy lấy danh sách href duy nhất từ ToC."""
    for item in toc_items:
        if isinstance(item, tuple):
            _get_unique_hrefs_from_toc(item, unique_hrefs)
        elif isinstance(item, epub.Link):
            href = item.href.split('#')[0]
            if href not in unique_hrefs:
                unique_hrefs[href] = item.title

def _split_content_by_headings(soup_body, book, doc_item, temp_image_dir) -> List[Dict[str, Any]]:
    """Quét các thẻ h2, h3... để tách bài viết bên trong một chương lớn."""
    articles = []
    current_article_content = []
    h1_tag = soup_body.find(['h1', 'h2'])
    current_subtitle = h1_tag.get_text(strip=True) if h1_tag else "Phần mở đầu"

    for tag in soup_body.find_all(True, recursive=False):
        if tag.name in ['h2', 'h3', 'h4']:
            if current_article_content:
                articles.append({'subtitle': current_subtitle, 'content': current_article_content})
            current_subtitle = tag.get_text(strip=True)
            current_article_content = []
        
        current_article_content.extend(_extract_html_content_sequentially(tag, book, doc_item, temp_image_dir))

    if current_article_content:
        articles.append({'subtitle': current_subtitle, 'content': current_article_content})

    return articles

def _parse_by_heuristic_scan(book, temp_image_dir) -> List[Dict[str, Any]]:
    structured_content = []
    unique_hrefs = OrderedDict()
    _get_unique_hrefs_from_toc(book.toc, unique_hrefs)

    for href, title in unique_hrefs.items():
        doc_item = book.get_item_with_href(href)
        if not doc_item: continue
        
        soup = BeautifulSoup(doc_item.get_content(), 'xml')
        if soup.body:
            articles = _split_content_by_headings(soup.body, book, doc_item, temp_image_dir)
            for article in articles:
                 content_title = f"{title} - {article['subtitle']}"
                 structured_content.append({'title': content_title, 'content': article['content']})
            
    return structured_content
    
# ==============================================================================
# --- MASTER PARSE FUNCTION ---
# ==============================================================================
def parse_epub(filepath: str) -> Dict[str, Any]:
    """
    Hàm chủ đạo, thử các chiến lược phân tích khác nhau để tìm ra kết quả tốt nhất.
    """
    results = {'metadata': {}, 'content': []}
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        book = epub.read_epub(filepath)
        
        # --- (Phần trích xuất metadata và ảnh bìa đã ổn định) ---
        metadata = {}
        try: metadata['title'] = book.get_metadata('DC', 'title')[0][0]
        except: metadata['title'] = Path(filepath).stem
        try: metadata['author'] = book.get_metadata('DC', 'creator')[0][0]
        except: metadata['author'] = 'Không rõ'
        results['metadata'] = metadata
        cover_path = ""
        cover_item = None
        for meta in book.get_metadata('OPF', 'meta'):
            if meta[1].get('name') == 'cover':
                cover_id = meta[1].get('content')
                cover_item = book.get_item_with_id(cover_id)
                if cover_item: print("Tìm thấy ảnh bìa qua OPF metadata.")
                break
        if not cover_item:
            for item in book.guide:
                if item.get('type') == 'cover' and item.get('href'):
                    href = item.get('href')
                    cover_item = book.get_item_with_href(href)
                    if cover_item: print("Tìm thấy mục cover qua Guide.")
                    break
        if not cover_item:
            flat_toc_for_cover = []
            _flatten_toc_recursive(book.toc, flat_toc_for_cover)
            cover_item = _find_cover_from_toc(book, flat_toc_for_cover)
            if cover_item: print(f"Tìm thấy ảnh bìa qua quét ToC: {cover_item.get_name()}")
        if cover_item:
            if cover_item.get_name().lower().endswith(('.xhtml', '.html')):
                soup = BeautifulSoup(cover_item.get_content(), 'xml')
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    final_cover_item = _resolve_image_path(img_tag.get('src'), cover_item, book)
                    if final_cover_item: cover_path = _save_image_to_temp(final_cover_item, temp_image_dir, "epub_cover_")
            else: cover_path = _save_image_to_temp(cover_item, temp_image_dir, "epub_cover_")
        results['metadata']['cover_image_path'] = cover_path
        
        # --- LOGIC THÍCH ỨNG ---
        flat_toc = []
        _flatten_toc_recursive(book.toc, flat_toc)
        
        content_list = []
        
        doc_items = [item for item in book.get_items() if item.media_type == 'application/xhtml+xml']
        
        is_granular = (len(flat_toc) / len(doc_items)) > 1.5 if doc_items else False
        
        if is_granular:
            print("=> Áp dụng chiến lược: ToC-Driven (Mục lục chi tiết)")
            content_list = _parse_by_toc_traversal(book, temp_image_dir)
        else:
            print("=> Áp dụng chiến lược: Heuristic-Driven (Mục lục đơn giản)")
            content_list = _parse_by_heuristic_scan(book, temp_image_dir)

        results['content'] = content_list
        return results

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'metadata': {}, 'content': [{'title': 'Error', 'content': [('text', f"An error occurred: {e}")]}]}