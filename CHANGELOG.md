# Lịch sử thay đổi (Changelog)

Tất cả các thay đổi đáng chú ý của dự án sẽ được ghi lại tại đây.
Dự án này tuân theo [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] - 2026-01-20

### ⚙️ Quy trình & Hạ tầng (Workflow & Infra)
-   **Quy trình nghiêm ngặt**: Triển khai hệ thống `.agent/workflows/` để bắt buộc Agent tuân thủ quy trình.
-   **Tiêu chuẩn Code**: Thiết lập luật cứng về File Header, Docstrings, và Type Hints (`coding_standards.md`).
-   **Experiment**: Thử nghiệm thành công quy trình mới trên nhánh `exp/workflow-simulation`.

### 🎨 Giao diện & Trải nghiệm (UI/UX)
-   **Sidebar**: Thêm nút "Hiện tại" và "Đóng sách" giúp điều hướng nhanh chóng.
-   **Hiệu năng**: Chế độ "Featherweight" cho ResultsView, sử dụng Lazy Loading giúp mở file lớn ngay lập tức.
-   **Dark Mode**: Kích hoạt giao diện tối mặc định.

### 🐛 Sửa lỗi (Bug Fixes)
-   **ResultsView**: Khắc phục lỗi crash do dữ liệu tuple từ parser cũ, đảm bảo hiển thị nội dung chính xác.
-   **Navigation**: Thêm thông báo "Coming Soon" cho các nút chưa có chức năng (Library, Settings).

### 🧹 Dọn dẹp & Tối ưu (Cleanup & Optimization)
-   **Git**: Loại bỏ thư mục `test_samples/` (chứa file mẫu nặng >500MB) và các script debug khỏi lịch sử theo dõi.
-   **Quy định**: Cập nhật `project_rules.md` giới hạn kích thước file commit (<50MB).

### 📢 Phản hồi & Tương tác (UI Feedback)
-   **Log Panel**: Khu vực hiển thị log trực tiếp trên giao diện, giúp theo dõi quá trình xử lý mà không cần mở console.
-   **Loading Overlay**: Màn hình chờ chuyên nghiệp, hiển thị thanh tiến trình (Progress Bar) chi tiết khi Lưu file, không còn bị treo giao diện.
-   **Thread-Safety**: Tách tác vụ Lưu trữ (Save) sang luồng riêng nền (background thread).

## [0.1.0-alpha] - 2025-09-20

Đây là phiên bản Alpha đầu tiên, hoàn thiện các chức năng cốt lõi về trích xuất và lưu trữ dữ liệu từ file PDF và EPUB.

### ✨ Tính năng mới (Features)

-   **Lõi trích xuất PDF:**
    -   Xây dựng parser có khả năng đọc **Mục lục (Bookmarks)** để xác định chính xác các chương.
    -   Trích xuất toàn diện nội dung **văn bản** và **hình ảnh** từ mỗi chương.
    -   Hình ảnh được lưu vào thư mục tạm và được đại diện bằng **"Image Anchor"** (đường dẫn) trong cấu trúc dữ liệu.

-   **Lõi trích xuất EPUB:**
    -   Xây dựng parser "thích ứng" (v14.0) có khả năng xử lý nhiều dạng cấu trúc **Mục lục (ToC)** phức tạp, bao gồm cả các cấu trúc lồng nhau.
    -   Trích xuất toàn diện nội dung **văn bản** và **hình ảnh** từ mỗi chương được ToC định nghĩa.
    -   Tích hợp logic giải quyết đường dẫn tương đối để đảm bảo tìm thấy file ảnh chính xác.
    -   Hình ảnh cũng được xử lý dưới dạng **"Image Anchor"** tương tự như PDF.

-   **Giao diện Người dùng (UI):**
    -   Xây dựng giao diện chính sử dụng CustomTkinter.
    -   Tích hợp **Khung hiển thị có thể cuộn (Scrollable Frame)** để xác minh trực quan kết quả trích xuất, bao gồm cả văn bản và image anchor.

-   **Chức năng Lưu trữ:**
    -   Triển khai tính năng "Lưu kết quả ra thư mục".
    -   Tự động tạo cấu trúc thư mục `Tên sách / Tên chương`.
    -   Lưu toàn bộ nội dung văn bản vào file `content.txt` và sao chép các file hình ảnh tương ứng vào từng thư mục chương.

### 🐛 Sửa lỗi (Bug Fixes)

-   **Parser EPUB:** Trải qua nhiều phiên bản (từ v2.x đến v14.0) để sửa các lỗi nghiêm trọng liên quan đến việc không đọc được nội dung, bỏ sót hình ảnh, và xử lý sai các cấu trúc ToC phức tạp.
-   **Giao diện:**
    -   Khắc phục lỗi crash `_tkinter.TclError: row out of bounds` bằng cách tối ưu hóa logic parser EPUB để không tạo ra quá nhiều widget.
    -   Triển khai giải pháp thay thế (workaround) cho lỗi `_tkinter.TclError: Unspecified error` của `filedialog.askdirectory` bằng cách sử dụng ô nhập liệu, giúp ứng dụng hoạt động ổn định.
-   **Môi trường:** Hướng dẫn xử lý lỗi `Fatal error in launcher` bằng cách tạo lại môi trường ảo sau khi di chuyển thư mục dự án.