# file-path: src/extract_app/core/content_structurer.py
# version: 1.0
# last-updated: 2025-09-22
# description: Chứa thuật toán thông minh để tách bài viết trong chương PDF.

from typing import List, Dict, Any
from collections import Counter

def _find_dominant_font_size(content: List) -> float:
    """Tìm ra kích thước font chữ phổ biến nhất (coi là font nội dung)."""
    sizes = [
        item[1]['size'] for item in content 
        if item[0] == 'text' and item[1]['size'] > 0
    ]
    if not sizes:
        return 12.0 # Kích thước mặc định
    
    # Đếm tần suất xuất hiện của mỗi size
    size_counts = Counter(sizes)
    # Trả về size phổ biến nhất
    return size_counts.most_common(1)[0][0]

def structure_pdf_articles(chapter_content: List) -> List[Dict[str, Any]]:
    """
    Nhận nội dung của một chương lớn và tách thành các bài viết con.
    """
    if not chapter_content:
        return []

    dominant_size = _find_dominant_font_size(chapter_content)
    # Một tiêu đề phải có size lớn hơn ít nhất 15% so với text thường
    heading_threshold = dominant_size * 1.15 

    articles = []
    current_article_content = []
    current_subtitle = "Phần mở đầu"

    for content_type, data in chapter_content:
        is_heading = False
        if content_type == 'text':
            if data['size'] > heading_threshold:
                is_heading = True

        if is_heading:
            # Nếu có nội dung cũ, lưu lại bài viết trước đó
            if current_article_content:
                articles.append({'subtitle': current_subtitle, 'content': current_article_content})
            
            # Bắt đầu bài viết mới
            current_subtitle = data['content']
            current_article_content = [] # Reset nội dung
        else:
            # Nếu không phải tiêu đề, thêm vào nội dung bài viết hiện tại
            current_article_content.append((content_type, data))

    # Lưu lại bài viết cuối cùng sau khi vòng lặp kết thúc
    if current_article_content:
        articles.append({'subtitle': current_subtitle, 'content': current_article_content})
        
    return articles