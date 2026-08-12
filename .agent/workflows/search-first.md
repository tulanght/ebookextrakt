---
description: Research-before-coding workflow. Search for existing tools, libraries, and patterns before writing custom code.
---
# Workflow /search-first

Workflow này chuẩn hóa quy trình "nghiên cứu giải pháp sẵn có trước khi code", giúp hạn chế tối đa việc phát minh lại bánh xe. Trọng điểm cho ExtractPDF-EPUB.

## Core Rules & Patterns

1. **NEED ANALYSIS (Phân tích Yêu cầu)**:
   - Trước khi code bất kỳ tiện ích hay chức năng mới nào, phải phân tích rõ xem điều này đã có sẵn trong dự án chưa (Search bằng grep).

2. **Duyệt Thư viện Mở**:
   - Nếu xử lý Text/HTML/PDF phức tạp, lên PyPI tìm trước các công cụ mạnh (vd: `beautifulsoup4`, `pdfplumber`, `PyMuPDF`) thay vì tự parse tay hoàn toàn.

3. **Ra Quyết Định (DECISION MATRIX)**:
   - **Adopt**: Có library khớp hoàn hảo, License MIT/Apache → Dùng luôn.
   - **Extend**: Khớp 1 phần → Cài đặt và viết wrapper mỏng để bọc lại.
   - **Build**: Không có thư viện phù hợp → Tự build code custom.

## Khi Nào Kích Hoạt?
- Khi nhận yêu cầu làm một Phase mới theo Roadmap.
- Đứng trước một tính năng lớn chưa từng xử lý, thay vì code tay ngay lập tức.
