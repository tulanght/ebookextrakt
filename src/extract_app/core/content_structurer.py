# file-path: src/extract_app/core/content_structurer.py
# version: 1.1
# last-updated: 2025-09-22
# description: Tinh chỉnh logic để xử lý các chương không có tiêu đề phụ.

from typing import List, Dict, Any
from collections import Counter

def _find_dominant_font_size(content: List) -> float:
    sizes = [item[1]['size'] for item in content if item[0] == 'text' and item[1]['size'] > 0]
    if not sizes: return 12.0
    return Counter(sizes).most_common(1)[0][0]

def structure_pdf_articles(chapter_content: List) -> List[Dict[str, Any]]:
    if not chapter_content: return []

    dominant_size = _find_dominant_font_size(chapter_content)
    heading_threshold = dominant_size * 1.15 

    articles = []
    current_article_content = []
    current_subtitle = "" # Bắt đầu với tiêu đề rỗng
    
    # --- LOGIC MỚI ĐỂ TÌM TIÊU ĐỀ ---
    headings_found = any(item[0] == 'text' and item[1]['size'] > heading_threshold for item in chapter_content)

    # Nếu không có tiêu đề phụ nào, coi cả chương là một bài viết duy nhất
    if not headings_found:
        return [{'subtitle': '', 'content': chapter_content}]

    # Nếu có tiêu đề, tiến hành tách bài
    for content_type, data in chapter_content:
        is_heading = False
        if content_type == 'text':
            if data['size'] > heading_threshold:
                is_heading = True

        if is_heading:
            if current_article_content:
                articles.append({'subtitle': current_subtitle, 'content': current_article_content})
            current_subtitle = data['content']
            current_article_content = []
        else:
            current_article_content.append((content_type, data))

    if current_article_content:
        articles.append({'subtitle': current_subtitle, 'content': current_article_content})
        
    return articles