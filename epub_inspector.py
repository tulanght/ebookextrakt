# epub_inspector.py (version 3.0 - TOC Tree Inspector)
from ebooklib import epub
from pathlib import Path

# --- BẠN VUI LÒNG THAY ĐỔI ĐƯỜNG DẪN NÀY ---
EPUB_FILE_PATH = r"D:\Ebooks\Atlas Obscura (Joshua Foer,_ (Z-Library).epub"
# -----------------------------------------

def _print_toc_tree(toc_items, level=0):
    """
    Hàm đệ quy để in ra cấu trúc cây của Mục lục.
    """
    indent = "  " * level
    for item in toc_items:
        if isinstance(item, epub.Link):
            print(f"{indent}- [Link] Title: '{item.title}', Href: '{item.href}'")
        elif isinstance(item, tuple):
            # Mục Section không có tiêu đề, chỉ là một nhóm chứa các Link con
            print(f"{indent}[Section - Level {level+1}]")
            _print_toc_tree(item, level + 1)
        else:
            print(f"{indent}[Unknown Item]: {item}")

def inspect_epub_toc(filepath):
    try:
        book = epub.read_epub(filepath)
        print("="*60)
        print("BÁO CÁO CẤU TRÚC CÂY MỤC LỤC (TOC TREE)")
        print(f"File: {Path(filepath).name}")
        print("="*60)
        
        if not book.toc:
            print("!!! FILE NÀY KHÔNG CÓ MỤC LỤC (TOC) !!!")
        else:
            _print_toc_tree(book.toc)

        print("\n" + "="*60)
        print("KẾT THÚC BÁO CÁO")
        print("="*60)

    except Exception as e:
        import traceback
        print(f"\n\n--- LỖI NGOẠI LỆ ---")
        traceback.print_exc()

if __name__ == "__main__":
    inspect_epub_toc(EPUB_FILE_PATH)