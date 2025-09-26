# file-path: src/extract_app/core/epub_parsers/simple_toc_parser.py
# version: 13.0 (Hierarchical Tree Builder)
# last-updated: 2025-09-26
# description: Implements a true hierarchical parser that identifies sub-chapter headings and builds a nested tree structure (Chapter -> Sub-Chapter -> Article).

from ebooklib import epub
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Tuple
from pathlib import Path
import os
from collections import Counter

# --- CONFIGURATION ---
HEADING_SPLIT_THRESHOLD = 15

# --- HELPER FUNCTIONS (Stable) ---
def _save_image_to_temp(image_item, temp_image_dir: Path, prefix="epub_") -> str:
    image_bytes = image_item.get_content()
    image_filename = f"{prefix}{Path(image_item.get_name()).name}"
    image_path = temp_image_dir / image_filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    return str(image_path)

def _resolve_image_path(src: str, doc_item: epub.EpubHtml, book: epub.EpubBook):
    if not src: return None
    current_dir = Path(doc_item.get_name()).parent
    resolved_path_str = os.path.normpath(os.path.join(current_dir, src)).replace('\\', '/')
    return book.get_item_with_href(resolved_path_str)

def _extract_content_from_tags(tags: List[Tag], book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path) -> List:
    content_list = []
    for element in tags:
        if not isinstance(element, Tag):
            continue
        temp_soup = BeautifulSoup(str(element), 'xml')
        temp_tag = temp_soup.find(element.name)
        if not temp_tag: continue
        for img_tag in temp_tag.find_all('img'):
            if img_tag.get('src'):
                image_item = _resolve_image_path(img_tag.get('src'), doc_item, book)
                if image_item:
                    anchor = _save_image_to_temp(image_item, temp_image_dir)
                    caption_tag = img_tag.find_parent('figure').find('figcaption') if img_tag.find_parent('figure') else None
                    caption = caption_tag.get_text(strip=True) if caption_tag else ""
                    content_list.append(('image', {'anchor': anchor, 'caption': caption}))
            img_tag.decompose()
        text = temp_tag.get_text(strip=True)
        if text:
            content_list.append(('text', text))
    return content_list

def _has_meaningful_content_between(start_tag: Tag, end_tag: Tag, separator_tag_name: str) -> bool:
    """Kiểm tra xem có nội dung thực sự giữa hai thẻ hay không."""
    for sibling in start_tag.find_next_siblings():
        if sibling == end_tag:
            break
        if not isinstance(sibling, Tag):
            continue
        if sibling.name != separator_tag_name and (sibling.get_text(strip=True) or sibling.find('img')):
            return True
    return False

# --- CORE LOGIC (v13.0 - Hierarchical) ---
def _process_chapter(soup_body: Tag, book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path) -> Tuple[List, List]:
    # Heuristic để quyết định có chia tách hay không (giữ nguyên)
    potential_separator_levels = ['h2', 'h3', 'h4', 'h5', 'h6']
    all_headings = soup_body.find_all(potential_separator_levels)
    if not all_headings:
        return _extract_content_from_tags(soup_body.find_all(True), book, doc_item, temp_image_dir), []
    heading_counts = Counter(h.name for h in all_headings)
    separator_tag = None
    for tag_level in potential_separator_levels:
        if heading_counts.get(tag_level, 0) > 1:
            separator_tag = tag_level
            break
    should_split = separator_tag and heading_counts.get(separator_tag, 0) > HEADING_SPLIT_THRESHOLD
    if not should_split:
        return _extract_content_from_tags(soup_body.find_all(True), book, doc_item, temp_image_dir), []

    # --- THUẬT TOÁN XÂY DỰNG CÂY CẤU TRÚC ---
    children_nodes = []
    separators = soup_body.find_all(separator_tag)
    current_sub_chapter_node = None

    # Xử lý "Phần mở đầu"
    intro_tags = [tag for tag in separators[0].find_previous_siblings()]
    intro_tags.reverse()
    if intro_tags:
        intro_content = _extract_content_from_tags(intro_tags, book, doc_item, temp_image_dir)
        if intro_content:
            # "Phần mở đầu" là một bài viết, không phải tiểu mục
            children_nodes.append({'title': 'Phần mở đầu', 'content': intro_content, 'children': []})
            
    # Xử lý các separator để xây dựng cây
    for i, separator in enumerate(separators):
        next_separator = separators[i+1] if i + 1 < len(separators) else None
        
        # Phân loại separator này là "Tiểu mục" hay "Bài viết"
        is_sub_chapter_heading = not _has_meaningful_content_between(separator, next_separator, separator_tag)

        if is_sub_chapter_heading:
            # Nếu nó là tiêu đề tiểu mục, tạo một node cha mới
            current_sub_chapter_node = {
                'title': separator.get_text(strip=True),
                'content': [], # Tiểu mục không có nội dung trực tiếp
                'children': []
            }
            children_nodes.append(current_sub_chapter_node)
        else:
            # Nếu nó là tiêu đề bài viết
            article_title = separator.get_text(strip=True)
            content_tags = [separator]
            for sibling in separator.find_next_siblings():
                if sibling == next_separator:
                    break
                content_tags.append(sibling)
            
            article_content = _extract_content_from_tags(content_tags, book, doc_item, temp_image_dir)
            article_node = {'title': article_title, 'content': article_content, 'children': []}

            if current_sub_chapter_node:
                # Thêm bài viết vào tiểu mục hiện tại
                current_sub_chapter_node['children'].append(article_node)
            else:
                # Nếu không có tiểu mục nào, thêm trực tiếp vào chương
                children_nodes.append(article_node)
                
    return [], children_nodes


def parse(book: epub.EpubBook, temp_image_dir: Path) -> List[Dict[str, Any]]:
    content_tree = []
    for link in book.toc:
        if any(keyword in link.title.lower() for keyword in ['cover', 'title', 'copyright', 'dedication', 'contents']):
            continue
        file_href = link.href.split('#')[0]
        doc_item = book.get_item_with_href(file_href)
        if not (doc_item and doc_item.media_type == 'application/xhtml+xml'):
            continue
        soup = BeautifulSoup(doc_item.get_content(), 'xml')
        if not soup.body:
            continue
        content, children = _process_chapter(soup.body, book, doc_item, temp_image_dir)
        node = {'title': link.title, 'content': content, 'children': children}
        if node['content'] or node['children']:
            content_tree.append(node)
    return content_tree