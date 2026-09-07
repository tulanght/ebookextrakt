---
description: Định hướng viết nội dung dài, tự động hóa Blogger cho dự án.
---
# Workflow /article-writing

Hướng dẫn AI tạo ra Content dài hạn (Auto-Blogger) bằng LLM sao cho giọng văn tự nhiên (human-like), không bị dính văn mẫu AI. Rất phù hợp cho chiến dịch đẩy bài (Publishing Pipeline) lên WordPress của ExtractPDF-EPUB.

## Core Rules & Patterns

1. **Quy tắc Bắt Buộc (Banned AI Patterns)**:
   - Xóa ngay các cụm từ sáo rỗng AI: "Trong bối cảnh phát triển nhanh chóng...", "Làm thay đổi cuộc chơi", "Mang tính cách mạng", "Tóm lại", "Nhìn chung".
   - Không được dùng câu hỏi kết luận vô bổ chỉ để kéo View. 
   - Không thêm văn mở đầu (throat-clearing) dài dòng trước khi dồn vào trọng tâm.

2. **Cách Viết Cụ Thể (Writing Process)**:
   - **Bằng chứng Thực Tế**: Dùng minh chứng, con số, screenshot, ví dụ cụ thể để dẫn dắt, không dùng tĩnh từ chung chung xáo rỗng.
   - Chặn đứt giải thích trước khi chèn ví dụ (Explain AFTER the example, not before).
   - Rút gọn câu càng súc tích càng tốt.

3. **Cấu Trúc (Structure)**:
   - Với Bài hướng dẫn (Technical Guides): Bắt đầu bằng những thứ User sẽ nhận được. Dùng cụ thể các đoạn Text, Image trong Markdown. Kết thúc bằng thao tác tiếp theo.
   - Bài Essay / Kiến thức: Bỏ 1 luận điểm ở mỗi phần heading, kết nối sự kiện hợp logic.

## Khi Nào Kích Hoạt?
- Sử dụng làm Prompt nền cho Gemini khi tính năng Keyword Cluster / Auto-Blogger của Phase 6 được khởi chạy.
