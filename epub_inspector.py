# epub_inspector.py (version 9.0 - Robust String Comparison)
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path
import re

# --- CẤU HÌNH ---
EPUB_FILE_PATH = r"D:/Ebooks/Atlas Obscura Wild Life An Explorer’s Guide to the World’s Living Wonders (Cara Giaimo, Joshua Foer) (Z-Library).epub" 
CHAPTER_TITLE_TO_INSPECT = "CHAPTER 1: Forests & Rainforests" 
# ----------------------------------------------------

def _flatten_toc_recursive(toc_items, flat_list):
    if isinstance(toc_items, epub.Link): flat_list.append(toc_items)
    elif hasattr(toc_items, '__iter__'):
        for item in toc_items: _flatten_toc_recursive(item, flat_list)

def normalize_string(s: str) -> str:
    """Hàm làm sạch chuỗi: xóa khoảng trắng thừa và chuyển thành chữ thường."""
    return re.sub(r'\s+', '', s).lower()

def inspect_chapter_html(filepath, chapter_title):
    try:
        book = epub.read_epub(filepath)
        print("="*60)
        print("BÁO CÁO CHẨN ĐOÁN HTML CHƯƠNG")
        print(f"File: {Path(filepath).name}")
        print(f"Chương cần kiểm tra: '{chapter_title}'")
        print("="*60)
        
        flat_toc = []
        _flatten_toc_recursive(book.toc, flat_toc)
        
        target_link = None
        normalized_target_title = normalize_string(chapter_title)

        for link in flat_toc:
            # --- LOGIC SO SÁNH ĐÃ SỬA LỖI ---
            normalized_link_title = normalize_string(link.title)
            if normalized_link_title == normalized_target_title:
                target_link = link
                break
        
        if not target_link:
            print(f"!!! LỖI: Không tìm thấy chương với tiêu đề '{chapter_title}' trong Mục lục.")
            print("\n--- CÁC TIÊU ĐỀ CÓ SẴN (đã làm sạch) ---")
            for link in flat_toc:
                print(f"- '{normalize_string(link.title)}'") # In ra chuỗi đã được làm sạch để debug
            print("="*60)
            return

        href = target_link.href.split('#')[0]
        doc_item = book.get_item_with_href(href)
        
        if not doc_item:
            print(f"!!! LỖI: Không tìm thấy nội dung cho href '{href}'.")
            return

        print(f"\n--- NỘI DUNG HTML THÔ CỦA CHƯƠNG '{chapter_title}' ---")
        soup = BeautifulSoup(doc_item.get_content(), 'xml')
        if soup.body:
            print(soup.body.prettify())
        else:
            print("!!! Không tìm thấy thẻ <body> trong chương này.")

        print("\n" + "="*60)
        print("KẾT THÚC BÁO CÁO")
        print("="*60)

    except Exception as e:
        import traceback
        print(f"\n\n--- LỖI NGOẠI LỆ ---")
        traceback.print_exc()

if __name__ == "__main__":
    inspect_chapter_html(EPUB_FILE_PATH, CHAPTER_TITLE_TO_INSPECT)