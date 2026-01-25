# Lộ trình Phát triển (Roadmap)
# version: 1.0
# last-updated: 2025-09-20
# description: Vạch ra các giai đoạn phát triển chính cho dự án.

## Tầm nhìn Dự án
Phát triển `ExtractPDF-EPUB App` thành một **Trung tâm Nội dung Thông minh (Intelligent Content Hub)**, không chỉ bóc tách dữ liệu một cách chính xác mà còn hỗ trợ tối ưu hóa, quản lý, và tự động hóa các quy trình sản xuất nội dung số.

---
## Lộ trình Phát triển (Các Giai đoạn Tiếp theo)

### Giai đoạn 1: Đại tu Giao diện & Trải nghiệm Người dùng (UI/UX Overhaul)
*Mục tiêu: Tối ưu hóa hiệu năng, làm cho ứng dụng nhẹ, nhanh và thông minh hơn trong tương tác.*

* **[x] Triển khai Chế độ xem "Featherweight" (Đã hoàn thành):**
    * Thay đổi cơ chế hiển thị: Sử dụng "Lazy Loading" để hiển thị cây nội dung tức thì.
    * Chỉ hiển thị cấu trúc: Tên chương/bài và Image Anchor.
    * Đã tích hợp tính năng đếm từ/ảnh (ví dụ: `[Text: 250 words]`).

* **[x] Xây dựng Hệ thống Log Tích hợp:**
    * Đưa khu vực log vào bên trong giao diện chính.
    * Log sẽ hiển thị thông tin tóm tắt, thông minh (ví dụ: "Trích xuất thành công 15 chương, tìm thấy 45 hình ảnh.") thay vì log chi tiết.

* **[x] Nâng cấp Toàn diện Luồng làm việc:**
    * Thêm **thanh tiến trình (progress bar)** cho các tác vụ tải và lưu file.
    * Thêm **popup thông báo** khi lưu thành công, kèm tùy chọn "Mở thư mục".
    * Cải tiến chức năng lưu: Hỗ trợ thư mục lưu mặc định, tự tạo nếu chưa có, và có danh sách dropdown để chọn lại các thư mục đã dùng gần đây.
    * Cải tiến các nút bấm để linh hoạt hơn (hỗ trợ nhấn Enter).

* **[x] Xây dựng Lịch sử Trích xuất:**
    * Tạo một danh sách hiển thị các ebook đã được xử lý trước đó để truy cập nhanh.

### Giai đoạn 2: Nâng cao Lõi Phân tích & Lưu trữ (Advanced Parsing & Storage)
*Mục tiêu: Tăng cường độ chính xác của parser và mở rộng khả năng lưu trữ.*

* **[ ] Phát triển Thuật toán Tách "Bài viết" Thông minh:**
    * Xây dựng logic để tự động nhận diện và tách các bài viết lẻ bên trong một file chương lớn dựa trên các thẻ tiêu đề (`<h2>`, `<h3>`...) hoặc các dấu hiệu khác.

* **[ ] Tích hợp Cơ sở dữ liệu SQLite:**
    * Xây dựng module `database.py`.
    * Triển khai chức năng lưu trữ toàn bộ nội dung đã bóc tách (văn bản, đường dẫn ảnh, chú thích,...) vào một file CSDL SQLite trên máy.

* **[ ] (Tương lai) Đồng bộ Hóa Cloud:**
    * Nghiên cứu và phát triển tính năng đồng bộ hóa CSDL với Google Drive hoặc các dịch vụ cloud khác.

### Giai đoạn 3: Mở rộng Hệ sinh thái & Tự động hóa (Ecosystem & Automation)
*Mục tiêu: Kết nối dữ liệu đã xử lý với các nền tảng khác.*

* **[ ] Xây dựng Tab "Tiện ích Dịch thuật AI":**
    * Tích hợp Gemini API và có thể cả Selenium.
    * Xây dựng chức năng dịch tự động các bài viết đã được lưu trong CSDL.
    * Tạo thư viện bài viết theo chủ đề.

* **[ ] Tích hợp WordPress & Tự động Đăng bài:**
    * Xây dựng module có khả năng kết nối và đăng bài lên một trang WordPress (có thể bắt đầu với server local).
    * Nghiên cứu khả năng đẩy bài từ server local lên server production.

* **[ ] (Tương lai) Tích hợp Mạng xã hội:**
    * Nghiên cứu và phát triển tính năng đăng bài lên Facebook.

---
## ✅ Thành tựu đã Đạt được (v0.1.0-alpha)

* **Hoàn thiện Lõi trích xuất Đa định dạng:** Xây dựng thành công parser "thích ứng" có khả năng xử lý và bóc tách chính xác nội dung (văn bản & hình ảnh) từ nhiều loại file PDF (dựa trên Bookmarks) và EPUB (dựa trên ToC phức tạp).
* **Xây dựng Hệ thống "Image Anchor":** Triển khai cơ chế lưu ảnh vào thư mục tạm và trả về "anchor" (đường dẫn) để tối ưu hiệu năng.
* **Hoàn thiện Chức năng Lưu trữ ra Thư mục:** Xây dựng module lưu trữ có khả năng tạo cấu trúc thư mục theo chương và lưu đầy đủ file text, hình ảnh.
* **Xây dựng Giao diện Xác minh Dữ liệu:** Tạo giao diện cơ bản cho phép người dùng kiểm tra trực quan kết quả trích xuất.

## ✅ Thành tựu Mới (v1.1.0 - UI Modernization & Optimization)
* **Tối ưu hóa Hiệu năng (Featherweight):** Giảm thời gian hiển thị kết quả EPUB lớn (>400MB) xuống dưới 1 giây nhờ Lazy Loading.
* **Cải tiến Điều hướng:** Thêm Sidebar "Active Book" và nút "Close Book", giải quyết vấn đề điều hướng bị lag/bí.
* **Cơ sở hạ tầng (Infrastructure):**
    * Thiết lập quy trình làm việc nghiêm ngặt (Agentic Workflows).
    * Dọn dẹp Git History, giảm dung lượng repo bằng cách loại bỏ file mẫu nặng.
    * Tích hợp Dark Mode mặc định.