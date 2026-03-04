# Lịch sử thay đổi (Changelog)

Tất cả các thay đổi đáng chú ý của dự án sẽ được ghi lại tại đây.
Dự án này tuân theo [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.2.0] - 2026-03-04

### 🧠 Phân tích PDF (PDF Semantic Splitting)
-   **Nested Bookmarks**: Hỗ trợ chia bài viết dạng cây (hierarchical) dựa trên cấu trúc Bookmark lồng nhau của PDF.
-   **Heuristic Splitting**: Tự động phân tách các chương quá dài không có tiểu mục bằng cách phân tích kích thước (font-size) và độ đậm (bold) của font chữ để nhận diện tiêu đề ẩn.
-   **Giao diện Mục lục phân cấp**: Cập nhật Library View (`library_view.py`) để hiển thị cấu trúc thư mục cha/con, theo dõi tiến độ dịch chi tiết cho từng cấp bài viết (leaf articles).
-   **Testing**: Bổ sung bộ Unit test tự động cho `pdf_parser.py` đảm bảo độ chính xác các logic phân cấp.

## [2.1.0] - 2026-02-27

### 🎨 Đại tu Giao diện — Dark Navy Theme (UI/UX Redesign)
-   **Design System (`theme.py`)**: Tạo file trung tâm chứa toàn bộ bảng màu Dark Navy (`Colors`), chuẩn font (`Fonts`), và khoảng cách (`Spacing`). Tất cả UI components import từ đây.
-   **Sidebar (`sidebar.py`)**: Viết lại hoàn toàn — Icon+Text layout, nhãn phân mục (MENU/ĐANG MỞ), highlight active state bằng xanh dương `#3B82F6`.
-   **Dashboard (`dashboard_view.py`)**: Chuyển sang bố cục Card — 3 thẻ thông tin (Import/Thư viện/Đã dịch) kèm hover effect, danh sách file gần đây hiện đại.
-   **Top Bar, Loading Overlay, Log Panel**: Đồng bộ Dark Navy theme.
-   **Main Window (`main_window.py`)**: Áp dụng nền `#0D1117`, loại bỏ `sv_ttk`, đổi tên "E-Extract", tăng kích thước cửa sổ 1200x800.

### ⚡ Tối ưu Dịch thuật
-   **Parallel Cloud Translation**: Dịch 3 chunk cùng lúc (ThreadPoolExecutor).
-   **Tăng Chunk Size**: Cloud chunks giờ là 15.000 ký tự (từ 3.000), giảm số lần gọi API.
-   **Loại bỏ Delay**: Bỏ khoảng nghỉ 2 giây giữa các chunk.
-   **Model Selector (Gemini 2.5)**: Thêm dropdown chọn model mới (Gemini 2.5 Pro/Flash, 2.0 Flash) vào `settings_view.py`.
-   **Auto-Fallback**: Tự động chuyển sang model khác nếu model chính bị lỗi 404.

### 🐛 Sửa lỗi
-   **TclError Crash**: Thêm `winfo_exists()` guard vào `library_view._render_content()`.
-   **Webview Markdown**: Cải thiện JavaScript parser cho headings, lists, bold, italic, paragraphs.
-   **Image Anchor Protection**: Thay tags `[Image: ...]` bằng placeholder `__IMG_ID_X__` trước khi gửi AI dịch.

## [0.2.0] - 2026-02-10

### ⚙️ Quy trình & Hạ tầng (Workflow & Infra)
-   **Quy trình nghiêm ngặt**: Triển khai hệ thống `.agent/workflows/` để bắt buộc Agent tuân thủ quy trình.
-   **Tiêu chuẩn Code**: Thiết lập luật cứng về File Header, Docstrings, và Type Hints (`coding_standards.md`).
-   **Experiment**: Thử nghiệm thành công quy trình mới trên nhánh `exp/workflow-simulation`.

-   **Navigation**: Thêm thông báo "Coming Soon" cho các nút chưa có chức năng (Library, Settings).

### 🧹 Dọn dẹp & Tối ưu (Cleanup & Optimization)
-   **Git**: Loại bỏ thư mục `test_samples/` (chứa file mẫu nặng >500MB) và các script debug khỏi lịch sử theo dõi.
-   **Quy định**: Cập nhật `project_rules.md` giới hạn kích thước file commit (<50MB).

### 📢 Phản hồi & Tương tác (UI Feedback)
-   **Log Panel**: Khu vực hiển thị log trực tiếp trên giao diện, giúp theo dõi quá trình xử lý mà không cần mở console.
-   **Loading Overlay**: Màn hình chờ chuyên nghiệp, hiển thị thanh tiến trình (Progress Bar) chi tiết khi Lưu file, không còn bị treo giao diện.
-   **Thread-Safety**: Tách tác vụ Lưu trữ (Save) sang luồng riêng nền (background thread).

### 🕒 Lịch sử & Tiện ích (History & Utils)
-   **Extract History**: Tự động lưu lại các file đã mở/trích xuất gần đây.
-   **Dashboard Quick Access**: Cho phép mở lại file nhanh chóng từ Dashboard mà không cần duyệt file lại.

### 🧠 Lõi Phân tích (Core Parsing)
-   **Smart Article Splitting**: Tự động chia nhỏ các chương dài thành các bài viết (sections) dựa trên tiêu đề (`<h2>`, `<h3>`), giúp nội dung dễ quản lý hơn.
-   **Image Extraction**: Cải thiện thuật toán trích xuất ảnh, hỗ trợ lấy ảnh ngay cả khi nằm trong các thẻ `<img>` trực tiếp không có wrapper.
-   **Structured Storage (SQLite)**: Tích hợp `extract.db` để lưu trữ sách, chương và bài viết dưới dạng có cấu trúc, tạo tiền đề cho các tính năng nâng cao (tìm kiếm, dịch thuật).
-   **Library Browser**: Giao diện quản lý sách đã trích xuất, cho phép tìm kiếm, xem chi tiết mục lục và trạng thái bài viết ngay trong ứng dụng.
-   **AI Translation**: Tích hợp Google Gemini API để dịch tự động các bài viết trong thư viện. Cho phép người dùng nhập API Key cá nhân (Miễn phí) để sử dụng model `gemini-1.5-flash`.

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