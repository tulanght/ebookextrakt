# epub_inspector.py (version 18.0 - Definitive HTML Slice Exporter)
from ebooklib import epub
from bs4 import BeautifulSoup, Tag
from pathlib import Path
import re

# --- CẤU HÌNH ---
EPUB_FILE_PATH = r"D:/Ebooks/DK Hello Tiny World · An En_ (Z-Library).epub"

# Liệt kê chính xác tên các chương bạn muốn trích xuất HTML đầy đủ
CHAPTER_TITLES_TO_INSPECT = [
    "ENGLAND",
    "IRELAND",
    "SCOTLAND"
]

OUTPUT_LOG_FILE = "log.txt"
# ----------------------------------------------------

def _flatten_toc_recursive(toc_items, flat_list):
    if isinstance(toc_items, epub.Link):
        flat_list.append(toc_items)
    elif hasattr(toc_items, '__iter__'):
        for item in toc_items:
            _flatten_toc_recursive(item, flat_list)

def normalize_string(s: str) -> str:
    """Hàm làm sạch chuỗi để so sánh."""
    return re.sub(r'\s+', ' ', s).strip().lower()

def export_html_slices(filepath, chapters_to_inspect, output_file):
    try:
        book = epub.read_epub(filepath)
        print(f"Bắt đầu phân tích file: {Path(filepath).name}")
        
        flat_toc = []
        _flatten_toc_recursive(book.toc, flat_toc)
        
        toc_map = {normalize_string(link.title): link for link in flat_toc}
        
        # Nhóm các chương cần phân tích theo file XHTML của chúng
        files_to_process = {}
        for title in chapters_to_inspect:
            normalized_title = normalize_string(title)
            link = toc_map.get(normalized_title)
            if link and '#' in link.href:
                file_href, anchor_id = link.href.split('#', 1)
                if file_href not in files_to_process:
                    files_to_process[file_href] = []
                files_to_process[file_href].append({'title': title, 'anchor_id': anchor_id})
            else:
                 print(f"!!! Cảnh báo: Không tìm thấy chương '{title}' hoặc href không hợp lệ.")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("="*80 + "\n")
            f.write("BÁO CÁO PHÂN TÍCH HTML CHI TIẾT (v18.0)\n")
            f.write(f"File EPUB: {Path(filepath).name}\n")
            f.write("="*80 + "\n\n")

            for file_href, chapters in files_to_process.items():
                doc_item = book.get_item_with_href(file_href)
                if not doc_item:
                    print(f"!!! Lỗi: Không tìm thấy file content '{file_href}'")
                    continue
                
                soup = BeautifulSoup(doc_item.get_content(), 'xml')
                all_tags = soup.find_all(True) # Lấy tất cả các thẻ theo thứ tự xuất hiện
                
                # Tìm tất cả các thẻ mỏ neo trong file
                all_anchor_tags_in_doc = [tag for tag in all_tags if tag.get('id')]
                
                for chapter_info in chapters:
                    title = chapter_info['title']
                    anchor_id = chapter_info['anchor_id']
                    
                    print(f"Đang xử lý chương: '{title}'...")
                    f.write(f"--- BẮT ĐẦU NỘI DUNG CHƯƠNG: '{title}' (Anchor: {anchor_id}) ---\n\n")

                    try:
                        # Tìm vị trí của mỏ neo bắt đầu và kết thúc
                        start_index = -1
                        end_index = len(all_tags) # Mặc định là cuối file

                        # Tìm vị trí index của anchor hiện tại
                        for i, tag in enumerate(all_anchor_tags_in_doc):
                            if tag['id'] == anchor_id:
                                # Vị trí bắt đầu là thẻ anchor đó
                                start_node = tag
                                start_index = all_tags.index(start_node)
                                # Tìm anchor tiếp theo để làm điểm kết thúc
                                if i + 1 < len(all_anchor_tags_in_doc):
                                    end_node = all_anchor_tags_in_doc[i+1]
                                    end_index = all_tags.index(end_node)
                                break
                        
                        if start_index != -1:
                            # Trích xuất lát cắt nội dung
                            content_slice = all_tags[start_index + 1 : end_index]
                            for tag in content_slice:
                                f.write(tag.prettify())
                                f.write("\n")
                        else:
                            f.write(f"--- KHÔNG TÌM THẤY MỎ NEO '{anchor_id}' ---\n")

                    except Exception as e_slice:
                         f.write(f"--- LỖI KHI TRÍCH XUẤT: {e_slice} ---\n")

                    f.write(f"\n--- KẾT THÚC NỘI DUNG CHƯƠNG: '{title}' ---\n\n")
            
        print(f"\nHoàn tất! Kết quả đã được ghi vào file: {output_file}")

    except Exception as e:
        import traceback
        print("\n--- LỖI NGOẠI LỆ ---")
        traceback.print_exc()

if __name__ == "__main__":
    export_html_slices(EPUB_FILE_PATH, CHAPTER_TITLES_TO_INSPECT, OUTPUT_LOG_FILE)