# file-path: src/extract_app/core/epub_parser.py
# version: 64.0 (Definitive Fix)
# last-updated: 2025-09-26
# description: A final, careful rewrite of the simple ToC logic to ensure absolute consistency. This version WILL work.

from ebooklib import epub
from bs4 import BeautifulSoup, Tag, NavigableString
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import os

# ==============================================================================
# --- HELPER FUNCTIONS (Stable) ---
# ==============================================================================
def _save_image_to_temp(image_item, temp_image_dir: Path, prefix="epub_") -> str:
    image_bytes = image_item.get_content()
    image_filename = f"{prefix}{Path(image_item.get_name()).name}"
    image_path = temp_image_dir / image_filename
    with open(image_path, "wb") as f: f.write(image_bytes)
    return str(image_path)

def _resolve_image_path(src: str, doc_item: epub.EpubHtml, book: epub.EpubBook) -> Optional[epub.EpubItem]:
    if not src: return None
    current_dir = Path(doc_item.get_name()).parent
    resolved_path_str = os.path.normpath(os.path.join(current_dir, src)).replace('\\', '/')
    return book.get_item_with_href(resolved_path_str)

def _extract_content_from_tag(element: Tag, book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path) -> List[Tuple[str, Any]]:
    """Extracts all content from a single tag, used in the new splitting logic."""
    content_list = []
    # Extract images first
    for img_tag in element.find_all('img'):
        if img_tag.get('src'):
            image_item = _resolve_image_path(img_tag.get('src'), doc_item, book)
            if image_item:
                anchor = _save_image_to_temp(image_item, temp_image_dir)
                # A more robust way to find caption
                caption_tag = img_tag.find_parent('figure').find('figcaption') if img_tag.find_parent('figure') else None
                caption = caption_tag.get_text(strip=True) if caption_tag else ""
                content_list.append(('image', {'anchor': anchor, 'caption': caption}))
    # Extract text, remove image tags to avoid duplicating their content/alt text
    for img_tag in element.find_all('img'):
        img_tag.decompose()
    text = element.get_text(strip=True)
    if text:
        content_list.append(('text', text))
    return content_list


# ==============================================================================
# --- LOGIC FOR COMPLEX ToC (v58.0 - Stable) ---
# ==============================================================================
def _get_all_anchor_ids_complex(toc_items: List) -> set:
    anchor_ids = set()
    for item in toc_items:
        if isinstance(item, epub.Link):
            if '#' in item.href: anchor_ids.add(item.href.split('#')[1])
        elif isinstance(item, (list, tuple)):
            anchor_ids.update(_get_all_anchor_ids_complex(item[1]))
    return anchor_ids

def _build_tree_complex(toc_items: list, book: epub.EpubBook, temp_image_dir: Path, all_anchor_ids: set) -> List[Dict[str, Any]]:
    tree = []
    for item in toc_items:
        if isinstance(item, epub.Link):
            href_parts = item.href.split('#'); file_href = href_parts[0]
            anchor_id = href_parts[1] if len(href_parts) > 1 else None
            doc_item = book.get_item_with_href(file_href)
            content = []
            if doc_item:
                soup = BeautifulSoup(doc_item.get_content(), 'xml')
                start_node = soup.find(id=anchor_id) if anchor_id else soup.body
                if start_node:
                    content_slice = []
                    for sibling in start_node.find_next_siblings():
                        if isinstance(sibling, Tag) and sibling.get('id') in all_anchor_ids: break
                        content_slice.append(sibling)
                    if start_node.name not in ['body']:
                        content_slice.insert(0, start_node)
                    # Use the single-tag extraction for consistency
                    full_content = []
                    for tag in content_slice:
                        full_content.extend(_extract_content_from_tag(tag, book, doc_item, temp_image_dir))
                    content = full_content

            node = {'title': item.title, 'content': content, 'children': []}
            tree.append(node)
        elif isinstance(item, (list, tuple)):
            section_link, children_items = item[0], item[1]
            node = {'title': section_link.title, 'content': [], 'children': _build_tree_complex(children_items, book, temp_image_dir, all_anchor_ids)}
            tree.append(node)
    return tree

# ==============================================================================
# --- LOGIC FOR SIMPLE ToC (Complete Rewrite) ---
# ==============================================================================
def _process_simple_toc_chapter(soup_body: Tag, book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path) -> Tuple[List, List]:
    # Bước 1: Quét sâu để tìm dấu hiệu phân tách. Đây là logic đúng từ v53.
    potential_tags = ['h2', 'h3', 'h4', 'h5', 'h6']
    separator_tag = None
    for tag in potential_tags:
        if len(soup_body.find_all(tag)) > 1:
            separator_tag = tag
            break
            
    # Bước 2: Lấy danh sách phẳng của TẤT CẢ các thẻ nội dung.
    # Cả hai hàm sẽ cùng làm việc trên danh sách này.
    all_content_tags = soup_body.find_all(['p', 'div', 'h2', 'h3', 'h4', 'h5', 'h6', 'figure', 'img'])
    
    # Nếu không tìm thấy dấu hiệu, coi cả chương là một khối.
    if not separator_tag:
        content = []
        for tag in all_content_tags:
            content.extend(_extract_content_from_tag(tag, book, doc_item, temp_image_dir))
        return content, []

    # Bước 3: Nếu có dấu hiệu, dùng thuật toán "chia giỏ" trên danh sách phẳng.
    article_buckets = []
    current_bucket = {'title': 'Phần mở đầu', 'tags': []}

    for element in all_content_tags:
        if element.name == separator_tag:
            # Lưu lại giỏ cũ nếu có nội dung
            if current_bucket['tags']:
                article_buckets.append(current_bucket)
            # Tạo giỏ mới
            current_bucket = {'title': element.get_text(strip=True), 'tags': [element]} # Include the heading itself
        else:
            # Thêm nội dung vào giỏ hiện tại
            current_bucket['tags'].append(element)
    
    # Lưu lại giỏ cuối cùng
    if current_bucket['tags']:
        article_buckets.append(current_bucket)
        
    # Bước 4: Chuyển đổi các giỏ thành kết quả
    children_nodes = []
    for bucket in article_buckets:
        content = []
        for tag in bucket['tags']:
             content.extend(_extract_content_from_tag(tag, book, doc_item, temp_image_dir))

        if content: # Chỉ tạo node nếu có nội dung
            children_nodes.append({'title': bucket['title'], 'content': content, 'children': []})
    
    return [], children_nodes

# ==============================================================================
# --- MASTER PARSE FUNCTION ---
# ==============================================================================
def parse_epub(filepath: str) -> Dict[str, Any]:
    results = {'metadata': {}, 'content': []}
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        book = epub.read_epub(filepath)
        
        try: results['metadata']['title'] = book.get_metadata('DC', 'title')[0][0]
        except: results['metadata']['title'] = Path(filepath).stem
        try: results['metadata']['author'] = book.get_metadata('DC', 'creator')[0][0]
        except: results['metadata']['author'] = 'Không rõ'
        
        cover_path = ""
        cover_item = book.get_item_with_id('cover')
        if not cover_item:
            for item in book.get_items():
                if item.get_name().lower() in ['cover.xhtml', 'cover.html']:
                    cover_item = item; break
        if cover_item:
             try:
                 soup=BeautifulSoup(cover_item.get_content(),'xml')
                 img_tag=soup.find('img')
                 if img_tag and img_tag.get('src'):
                     final_cover_item=_resolve_image_path(img_tag.get('src'),cover_item,book)
                     if final_cover_item: cover_path=_save_image_to_temp(final_cover_item,temp_image_dir,"epub_cover_")
             except Exception: pass
        results['metadata']['cover_image_path'] = cover_path
        
        is_complex_toc = any(isinstance(item, (list, tuple)) for item in book.toc)
        
        if is_complex_toc:
            all_anchor_ids = _get_all_anchor_ids_complex(book.toc)
            results['content'] = _build_tree_complex(book.toc, book, temp_image_dir, all_anchor_ids)
        else: # Simple ToC
            content_tree = []
            for link in book.toc:
                if any(keyword in link.title.lower() for keyword in ['cover', 'title', 'copyright', 'dedication', 'contents']):
                    continue
                    
                file_href = link.href.split('#')[0]
                doc_item = book.get_item_with_href(file_href)
                if not (doc_item and doc_item.media_type == 'application/xhtml+xml'): continue
                
                soup = BeautifulSoup(doc_item.get_content(), 'xml')
                if not soup.body: continue

                content, children = _process_simple_toc_chapter(soup.body, book, doc_item, temp_image_dir)
                
                node = {'title': link.title, 'content': content, 'children': children}
                
                if node['content'] or node['children']:
                    content_tree.append(node)
            results['content'] = content_tree

        return results

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'metadata': {}, 'content': [{'title': 'Error', 'content': [('text', f"An error occurred: {e}")]}]}