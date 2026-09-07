---
description: Scan your environment and codebase for security vulnerabilities, misconfigurations, and injection risks.
---
# Workflow /security-scan

Quản trị bảo mật cho các khoá API key (WordPress, Gemini, Anthropic) và quy trình quản lí file nhạy cảm.

## Core Rules & Patterns

1. **Nghiêm Cấm Hardcode**:
   - Không được hardcode API keys, mật khẩu FTP/DB vào file `.py`. Toàn bộ sử dụng `dotenv` `.env` hoặc hệ thống Registry / CLAUDE settings an toàn.

2. **Kiểm Tra Trích Xuất (Prompt Injection Vector)**:
   - File PDF/EPUB đầu vào có thể ẩn chứa Injection, nên quy trình xử lý Text phải làm sạch, bóc tách noise trước khi đưa vào System Prompt cho API gọi LLM.

3. **Cơ Chế Hook & Ignore**:
   - Nếu sinh log, không để lộ thông tin quan trọng. Thư mục Logs/Temp cần được định tuyến vào `.gitignore`.

## Khi Nào Kích Hoạt?
- Khi triển khai tính năng Local GenAI hoặc gọi WordPress REST API. AI phải rà soát qua workflow này để biết cách nạp Credentials an toàn.
