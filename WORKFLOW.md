# QUY TRÌNH LÀM VIỆC DỰ ÁN (Project Workflow)
# version: 2.0
# last-updated: 2025-09-18
# description: Phiên bản cải tiến, tập trung vào quy trình nghiên cứu, thử nghiệm và xác nhận trực quan cho các module phân tích (parser).

## 1. Triết lý Chung
* **Nguồn sự thật duy nhất:** Nhánh `main` là nền tảng ổn định, đã được kiểm thử và xác nhận.
* **Làm việc trên nhánh:** Mọi thay đổi đều phải được thực hiện trên nhánh riêng.
* **Xác nhận trước, hợp nhất sau:** Mọi thay đổi chỉ được hợp nhất vào `main` sau khi đã được người dùng kiểm tra và xác nhận trực quan là "đạt yêu cầu".
* **AI là Cộng tác viên:** Gemini AI phải tuân thủ nghiêm ngặt toàn bộ quy trình này.

---
## 2. Quy trình làm việc với Git & Môi trường

### 2.1. Đặt tên nhánh
* **Tính năng mới:** `feature/<ten-tinh-nang-ngan-gon>`
* **Sửa lỗi:** `fix/<ten-loi>`
* **Tài liệu/Quy trình:** `docs/<noi-dung-cap-nhat>`
* **Nghiên cứu/Thử nghiệm:** `exp/<y-tuong-thu-nghiem>` (Nhánh cho việc thử nghiệm các heuristic mới)

### 2.2. Quy ước Commit Message
* Sử dụng **Conventional Commits** (`<type>(<scope>): <subject>`) để giữ lịch sử commit rõ ràng.

### 2.3. Quản lý Thư viện (`requirements.txt`)
* Khi có thay đổi, chạy `pip install -r requirements.txt` để cập nhật môi trường.

---
## 3. Quy trình Cộng tác với Gemini AI (Cải tiến)

### 3.1. Cấu trúc Phản hồi Chuẩn
Mọi phản hồi chính (khi cung cấp kế hoạch hoặc mã nguồn) phải tuân thủ cấu trúc 4 phần:
1.  `Phần 1: Phân tích & Kế hoạch`
2.  `Phần 2: Gói Cập Nhật Mục Tiêu`
3.  `Phần 3: Hướng dẫn Hành động & Lệnh Git`
4.  `Phần 4: Kết quả Kỳ vọng & Cảnh báo`

### 3.2. Quy tắc Chờ Xác nhận (QUAN TRỌNG)
* Sau mỗi lần cung cấp mã nguồn (Phần 2) và hướng dẫn (Phần 3), AI **bắt buộc** phải dừng lại.
* AI **không được đề xuất bước tiếp theo hoặc tính năng mới** cho đến khi nhận được xác nhận rõ ràng từ người dùng rằng mã nguồn đã chạy thành công và kết quả đúng như kỳ vọng.

### 3.3. Cơ chế "Reset"
* Khi AI vi phạm quy tắc, người dùng sẽ sử dụng từ khóa `CHECK-WORKFLOW` để yêu cầu AI dừng lại, đọc lại file này và tự điều chỉnh.

---
## 4. Quy trình Đặc thù cho Module Phân tích & Trích xuất (MỚI)
**Đây là phần cải tiến quan trọng nhất, áp dụng riêng cho các file parser (`pdf_parser.py`, `epub_parser.py`) và structurer (`content_structurer.py`).**

### 4.1. Giai đoạn 1: Nghiên cứu & Đề xuất Heuristic
* **Vấn đề:** Trước khi viết code cho một tác vụ phức tạp (ví dụ: tìm chú thích ảnh trong PDF), AI không được tự ý đưa ra giải pháp.
* **Quy trình:**
    1.  AI phải phân tích vấn đề và trình bày **kế hoạch tiếp cận dựa trên heuristic** một cách chi tiết. (Ví dụ: "Để tìm chú thích, tôi đề xuất tìm khối văn bản có font size nhỏ nhất và nằm ngay dưới một hình ảnh trong phạm vi 50 pixels.")
    2.  AI phải giải thích **ưu, nhược điểm và các trường hợp ngoại lệ** của heuristic này.
    3.  Người dùng sẽ xem xét, góp ý và **phê duyệt** kế hoạch.

### 4.2. Giai đoạn 2: Phát triển & Kiểm thử Cô lập
* **Vấn đề:** Tránh việc áp dụng code mới vào toàn bộ ứng dụng ngay lập tức.
* **Quy trình:**
    1.  Sau khi kế hoạch được phê duyệt, AI sẽ cung cấp mã nguồn cho hàm xử lý.
    2.  AI phải cung cấp thêm một **đoạn mã kiểm thử nhỏ** để người dùng có thể chạy thử nghiệm chức năng này một cách độc lập với một file mẫu duy nhất, thay vì phải chạy toàn bộ ứng dụng.
    3.  Người dùng kiểm tra kết quả trên file mẫu.

### 4.3. Giai đoạn 3: Tích hợp, Phản hồi & Tinh chỉnh
* **Vấn đề:** Đảm bảo code hoạt động tốt khi tích hợp vào ứng dụng chính và xử lý các trường hợp thực tế.
* **Quy trình:**
    1.  Sau khi kiểm thử cô lập thành công, AI sẽ cung cấp gói cập nhật để tích hợp vào ứng dụng chính (ví dụ: cập nhật `main_window.py`).
    2.  Người dùng chạy ứng dụng, thử nghiệm với nhiều file khác nhau và đưa ra **phản hồi trực quan** (Ví dụ: "Heuristic hoạt động tốt với file A, nhưng nhận nhầm phần footer là chú thích ở file B.").
    3.  Vòng lặp quay lại Giai đoạn 1: AI tiếp nhận phản hồi, đề xuất một heuristic đã được tinh chỉnh, và quy trình lặp lại cho đến khi kết quả đạt yêu cầu.

### 4.4. Cập nhật Tài liệu Kỹ thuật
* Sau khi một heuristic phức tạp được chốt và hoạt động ổn định, AI có trách nhiệm đề xuất nội dung cập nhật cho file `TECHNICAL_NOTES.md` để ghi lại quyết định kiến trúc đó.