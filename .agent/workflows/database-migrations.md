---
description: Database migration best practices for schema changes safely targeting SQLite in this project.
---
# Workflow /database-migrations

Quy trình chuẩn hóa việc thay đổi cấu trúc bảng (Schema Migrations) đối với SQLite trong dự án ExtractPDF-EPUB. An toàn, không mất dữ liệu của người dùng.

## Core Rules & Patterns

1. **Mọi thay đổi Schema đều phải là Migration code**:
   - Không được bảo user "mở DB lên thêm cột". Phải viết code Python để tự động thực thi.

2. **Migration mở rộng (Expand Pattern) an toàn**:
   - Khi thêm cột mới, NÊN dùng `DEFAULT` value thay vì bắt `NOT NULL` cứng nhắc (do bảng có sẵn sẽ bị lỗi nếu thiếu default).
   - Nếu sửa tên cột / cấu trúc phức tạp trong SQLite, áp dụng kịch bản lập bảng nháp: Thêm bảng mới -> Xả dữ liệu qua -> Đổi tên bảng cũ -> Đổi tên bảng mới.

3. **Cập nhật dữ liệu hàng loạt cẩn thận**:
   - Nếu cần fill Data lớn (như đếm `word_count` cho các bài sẵn có), tạo vòng lặp SELECT + UPDATE thay vì 1 block quá lớn làm khoá DB hoặc Out Of Memory.

4. **Tích hợp vào `database.py`**:
   - Mọi logic DB phải cập nhật vào `_check_migrations` trong `database.py`. Đảm bảo code sẽ tự động chạy lúc khởi tạo app để tự sửa schema nếu nó là phiên bản cũ.

## Khi Nào Kích Hoạt?
- Bất cứ khi nào thêm Cột (Column) mới, Bảng (Table) mới phục vụ tính năng mới.
