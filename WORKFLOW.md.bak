# QUY TRÌNH LÀM VIỆC DỰ ÁN (Project Workflow)
# version: 3.0 (Antigravity Edition)
# description: Quy trình làm việc tích hợp khả năng Agentic, tập trung vào việc lập kế hoạch qua Artifacts và tự động xác nhận bằng Tools.

## 1. Triết lý Chung
*   **Nguồn sự thật duy nhất:** Nhánh `main` là nền tảng ổn định.
*   **Agentic First:** Antigravity đóng vai trò là một kỹ sư phần mềm chủ động (Agent), không chỉ là một chatbot thụ động. Agent có trách nhiệm đọc, viết, chạy lệnh và kiểm thử code.
*   **Artifact-Driven:** Mọi kế hoạch, trạng thái công việc và báo cáo kết quả phải được quản lý thông qua **Artifacts** (`task.md`, `implementation_plan.md`, `walkthrough.md`) thay vì chỉ hội thoại text.
*   **Xác nhận bằng Bằng chứng:** Agent phải tự chạy code/test để xác nhận kết quả và đưa vào `walkthrough.md` trước khi yêu cầu người dùng merge.

---

## 2. Quy trình làm việc với Git & Môi trường

> [!IMPORTANT]
> **COMPLIANCE ENFORCEMENT**:
> Agent MUST follow the strict workflows defined in `.agent/workflows/`.
> - **Starting Work**: Read `.agent/workflows/start_task.md`
> - **Coding**: Read `.agent/workflows/coding_standards.md`
> - **Testing**: Read `.agent/workflows/run_tests.md`
> - **Finishing**: Read `.agent/workflows/finish_task.md`

### 2.1. Đặt tên nhánh

### 2.1. Đặt tên nhánh
*   **Tính năng mới:** `feature/<ten-tinh-nang-ngan-gon>`
*   **Sửa lỗi:** `fix/<ten-loi>`
*   **Tài liệu/Quy trình:** `docs/<noi-dung-cap-nhat>`
*   **Nghiên cứu/Thử nghiệm:** `exp/<y-tuong-thu-nghiem>`

### 2.2. Commit Message
*   Tuân thủ tiêu chuẩn **Conventional Commits**: `<type>(<scope>): <subject>`

### 2.3. Quản lý Môi trường
*   Agent có quyền và trách nhiệm tự kiểm tra `requirements.txt` và đề xuất chạy `pip install` khi thêm thư viện mới.

---

## 3. Quy trình "Agentic Workflow" (Thay thế quy trình Chat cũ)

Thay vì cấu trúc phản hồi 4 phần (Plan/Code/Instruction/Expectation) trong chat, Agent sẽ thực hiện vòng lặp sau:

### 3.1. Giai đoạn PLANNING (Lập kế hoạch)
*   **Hành động:** Agent phân tích yêu cầu, đọc codebase hiện tại.
*   **Artifact:** Tạo hoặc cập nhật `implementation_plan.md`.
    *   **Goal:** Mô tả mục tiêu.
    *   **Proposed Changes:** Liệt kê cụ thể các file sẽ sửa/tạo.
    *   **Verification Plan:** Định nghĩa cách Agent sẽ tự test (lệnh nào, script nào).
*   **Review:** Agent sử dụng `notify_user` để mời người dùng review Plan. *Chỉ chuyển sang Execution khi User đồng ý.*

### 3.2. Giai đoạn EXECUTION (Thực thi)
*   **Hành động:**
    *   Agent chuyển Task Mode sang **EXECUTION**.
    *   Agent tự động tạo nhánh git (nếu cần).
    *   Agent viết code (`write_to_file`, `replace_file_content`).
    *   Agent **tự chạy code** (`run_command`) để bước đầu kiểm tra lỗi cú pháp/logic cơ bản.

### 3.3. Giai đoạn VERIFICATION (Xác minh & Báo cáo)
*   **Hành động:**
    *   Agent chuyển Task Mode sang **VERIFICATION**.
    *   Agent chạy các script kiểm thử đã định nghĩa trong Plan.
    *   Nếu lỗi -> Quay lại Execution sửa ngay lập tức.
*   **Artifact:** Tạo `walkthrough.md`.
    *   Ghi lại những thay đổi đã làm.
    *   **Quan trọng:** Bao gồm log chạy lệnh, screenshot (nếu là UI) chứng minh code hoạt động.
*   **Hoàn tất:** Agent thông báo cho người dùng (`notify_user`) review kết quả cuối cùng.

---

## 4. Quy trình Phát triển Module Phân tích (Updated)

Áp dụng sức mạnh của Tools cho các parser (`pdf_parser.py`, `epub_parser.py`, `content_structurer.py`).

### 4.1. Nghiên cứu & Prototyping
*   Thay vì chỉ đoán heuristic, Agent sử dụng `read_file` hoặc `run_command` (với các tool inspect PDF/EPUB) để nhìn vào dữ liệu thực tế.
*   Agent viết một script nhỏ (ví dụ `temp/debug_heuristic.py`) và chạy nó để xem output thực tế *trước khi* đề xuất phương án chính thức trong `implementation_plan.md`.

### 4.2. Kiểm thử Cô lập (Isolated Testing)
*   Agent tạo file test riêng cho chức năng mới.
*   Agent chạy file test này và ghi lại log vào `walkthrough.md`.
*   User chỉ cần xem kết quả log mà Agent gửi, không cần phải tự copy-paste chạy lệnh trừ khi muốn double-check.

### 4.3. Tích hợp & User Acceptance
*   Sau khi Agent tự tin với kết quả test cô lập, Agent tích hợp vào flow chính.
*   User chạy app kiểm tra lần cuối trên tập dữ liệu rộng hơn.

---

## 5. Từ khóa đặc biệt
*   `CHECK-WORKFLOW`: Yêu cầu Agent dừng lại, đọc lại file này nếu thấy Agent đi chệch hướng sang kiểu "chat thụ động" cũ.