---
description: Ý tưởng để hệ thống liên tục học hỏi từ các thói quen trích xuất của user và project styles.
---
# Workflow /continuous-learning-v2

Kiến trúc "học liên tục" biến các phiên làm việc (sessions) thành "Bản năng" (Instincts) có thể tái sử dụng.

## Core Rules & Patterns

1. **Ghi Nhận Bản Năng (Instincts) Theo Project**:
   - AI Agent phân tích khi gặp lỗi OCR PDF lặp đi lặp lại hoặc lỗi cấu trúc HTML đặc thù của EPUB. Thay vì mỗi lần giải quyết 1 lần, AI sẽ viết tóm tắt pattern xử lý thành một Skill / Instinct ghi nhớ vào Markdown (e.g. `docs/ai/implementation/learnt-patterns.md`).
   
2. **Atomic Rules (Nguyên tắc Nguyên tử)**:
   - Mỗi bản năng ghi lại đều phải nhỏ gọn:
     - *Trigger*: Gặp file nhà xuất bản X bị lỗi font A.
     - *Action*: Chạy regex xóa chuỗi "\u00A0".
   
3. **Phân loại Scope**:
   - Project-scoped: Các pattern riêng cho format sách của người dùng đang xử lý.
   - Global-scoped: Vấn đề code style chung (Docstrings, Typing).

## Khi Nào Kích Hoạt?
- Khi rà soát lỗi (Bug fixing) xong và nhận ra điều này có thể lặp lại trong tương lai.
- Gọi workflow này để cập nhật vào memory (Có thể thay thế bằng `/remember`).
