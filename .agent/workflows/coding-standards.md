---
description: Pythonic idioms, PEP 8 standards, type hints, and best practices for building robust Python applications.
---
# Workflow /coding-standards

Định chuẩn quá trình viết code Python cho toàn bộ dự án ExtractPDF-EPUB. AI DevKit cần tuân thủ triệt để khi thực thi code.

## Core Rules & Patterns

1. **Explicit is Better (Rõ Ràng & Minh Bạch)**:
   - KHÔNG dùng variable ngắn ngủn (e.g. `u`, `x`).
   - TRÁNH exception lặp (`except:` chung chung). Phải catch rõ `except ValueError:` v.v...

2. **Types & Annotations**:
   - Kỹ thuật bắt buộc cho toàn bộ dự án hiện tại là Type Hint `-> int:` hoặc `dict[str, Any]`. Python 3.9+ conventions.

3. **Context Managers & Pathlib**:
   - Xử lý file LUÔN LUÔN dùng `with open(.., 'r', encoding='utf-8') as f:`.
   - File Path phải dùng `pathlib.Path`, không dùng nối chuỗi `path + "/" + file`.

4. **Exception Handling & EAFP**:
   - Theo sát nguyên tắc `Easier to Ask Forgiveness than Permission (EAFP)`, bắt Lỗi bằng vòng try thay vì check conditions trước nếu có liên hệ File IO hay Network.

## Khi Nào Kích Hoạt?
- Tự động áp dụng trên toàn bộ các agent và tool write/modify python.
