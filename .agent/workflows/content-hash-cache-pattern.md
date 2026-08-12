---
description: Cache expensive file processing results using SHA-256 content hashes.
---
# Workflow /content-hash-cache-pattern

Sử dụng SHA-256 mã băm nội dung để lưu trữ đệm (caching), giúp tăng code performance cho AI, tránh dịch lại đoạn text đã dịch khi user chạy lại tiến trình.

## Core Rules & Patterns

1. **Sử dụng SHA-256 Content Hash làm Cache Key**:
   - Thay vì lưu cache theo *đường dẫn file* hoặc *ID bài viết*, hãy mã băm nội dung text thô `sha256(text.encode('utf-8')).hexdigest()`.
   - Lợi ích: Bất kể file bị đổi tên hay chuyển thư mục, nếu nội dung text giống hệt thì sẽ Hit Cache.

2. **Cache Storage qua SQLite**:
   - Trong ứng dụng ExtractPDF-EPUB, khi một đoạn text đã được dịch, dịch vụ dịch thuật nên kiểm tra xem có đoạn `original_text_hash` tương ứng nào trong CSDL (bảng riêng hoặc cache đệm) không trước khi gọi API.

3. **Tách biệt Data Processing và Cache (Service Layer Wrapper / SRP)**:
   - Các hàm parse text/dịch thuật phải hoàn toàn thuần tuý (không tự check cache). Việc kiểm tra cache phải được bọc bên ngoài.
   - Ví dụ:
     ```python
     def translate_with_cache(text, cache_enabled=True):
         if not cache_enabled:
             return call_llm(text)
         
         text_hash = get_sha256(text)
         cached = check_db(text_hash)
         if cached: return cached
         
         result = call_llm(text)
         save_to_db(text_hash, result)
         return result
     ```

## Khi Nào Kích Hoạt?
- Tích hợp vào quy trình dịch thuật AI.
- Xử lý phân tích ảnh/PDF tốn kém. Tái sử dụng kết quả Parse nếu file PDF chưa bị thay đổi.
