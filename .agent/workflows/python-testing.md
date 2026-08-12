---
description: Python testing strategies using pytest, TDD methodology, fixtures, mocking, parametrization.
---
# Workflow /python-testing

Quy trình tự động hóa Test cho ExtractPDF-EPUB, kết nối nhịp nhàng với tool viết Test có sẵn.

## Core Rules & Patterns

1. **Chu trình TDD (Test-Driven Development)**:
   - RED: Viết TestCase trước khi code (hoặc với AI, lên Outline các case hỏng).
   - GREEN: Chạy LLM fix cho pass.
   - REFACTOR: Chỉnh đốn Typing/Chuẩn hóa theo /coding-standards.

2. **Pytest Fixtures**:
   - Khi load file PDF Test mẫu, LUÔN dùng `pytest.fixture(scope="session")` cho database nháp (`:memory:`) hoặc file temp/sandbox để tránh rác ổ cứng dự án chính.

3. **Mocking External APIs**:
   - Khi test hàm dịch LLM, TUYỆT ĐỐI không gọi thẳng lên Google API. Phải dùng `unittest.mock.patch` mô phỏng trả về text.

## Khi Nào Kích Hoạt?
- Khi được User yêu cầu viết Test (hoặc chạy `/writing-test`). Giao tiếp workflow này để biết cách tổ chức thư mục Test trong `tests/unit/` hoặc `tests/integration/`.
