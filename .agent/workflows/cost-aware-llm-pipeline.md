---
description: Cost optimization patterns for LLM API usage — model routing by task complexity, budget tracking, retry logic, and prompt caching.
---
# Workflow /cost-aware-llm-pipeline

Workflow này định nghĩa các quy tắc để quản lý chi phí LLM (Gemini/Local LLM) khi trích xuất hoặc dịch sách nội dung lớn.

## Core Rules & Patterns

1. **Model Routing theo Độ Khó**: 
   - Kiểm tra xem đoạn văn bản cần dịch/xử lý có lớn hơn 10,000 ký tự không. Nếu có, sử dụng mô hình lớn (vd: Gemini Pro hoặc Local 12B).
   - Nếu đoạn văn bản ngắn, ngữ cảnh hẹp, dùng mô hình nhẹ hơn (Gemini Flash) để ưu tiên tốc độ và chi phí.

2. **Immutable Cost Tracking & DB Logging**:
   - Khi gọi API, luôn log `tokens_in`, `tokens_out`, `duration_seconds` vào bảng `api_usage` trong SQLite (như đã thiết kế trong database.py).
   - Có thể thiết lập Budget Alert để dừng nếu vượt ngưỡng.

3. **Narrow Retry Logic**:
   - Chỉ retry khi gặp lỗi tạm thời (Rate Limit `429`, Internal Server Error `500`).
   - KHÔNG retry khi lỗi `400` (Bad Request) hoặc `401` (Auth), tránh tốn thời gian vô ích.

4. **Prompt Caching**:
   - Nếu tái sử dụng System Prompt giống nhau cho hàng trăm bài viết trong cùng 1 cuốn sách, cần thiết lập thuộc tính `cache_control` cho prompt.

## Khi Nào Kích Hoạt?
- Khi viết mã cho module gọi API LLM (e.g `translation_service.py`, `local_genai.py`).
- Xử lý mảng (batch) dữ liệu sách khổng lồ.
