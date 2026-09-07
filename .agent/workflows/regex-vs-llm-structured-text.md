---
description: Decision framework for choosing between regex and LLM when parsing structured text.
---
# Workflow /regex-vs-llm-structured-text

Framework quyết định khi nào cần regex và khi nào cần LLM để bóc tách file EPUB/PDF, giúp giảm thiểu chi phí LLM không cần thiết.

## Core Rules & Patterns

> 💡 **Quy tắc vàng:** Regex xử lý 95-98% một cách rẻ và nhanh. Chỉ dùng LLM cho những edge cases có độ tự tin thấp (Low confidence).

1. **Luồng Kiến Trúc Khuyến Nghị**:
   ```
   Nguồn Văn Bản 
       │
       ▼
   [Regex Parser / EPUB HTML Parser] ─── Trích xuất cấu trúc (95-98% chính xác)
       │
       ▼
   [Text Cleaner] ─── Chỉnh sửa rác, đánh số trang
       │
       ▼
   [Confidence Scorer] ─── Chấm điểm tự tin
       │
       ├── High confidence (≥0.95) → Trực tiếp xuất
       │
       └── Low confidence (<0.95) → [Gửi LLM sửa chữa] → Xuất
   ```

2. **Confidence Scoring Design**:
   - Đối với việc tách chương PDF/EPUB, nếu số chương đánh không tuần tự, bị mất subtitle, file quá ngắn, hoặc lộn xộn các HTML Tags → Gắn nhãn LOW CONFIDENCE.

3. **Duyệt bởi LLM**:
   - Nếu `confidence < 0.95`, truyền nguyên đoạn text vào LLM (nên dùng model giá rẻ cực nhanh như Gemini Flash) với prompt:
     `"Extract the correct hierarchy of titles and text chunks from this messy OCR/EPUB output. Current extraction is [X]. Fix it."`

## Khi Nào Kích Hoạt?
- Khắc phục các lỗi hoặc case khó trong `pdf_parser.py` và `epub_parser.py`.
- Tách bài viết (semantic splitting) với các cuốn sách có syntax lộn xộn.
