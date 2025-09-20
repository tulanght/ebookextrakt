# ExtractPDF-EPUB App v0.1.0-alpha

**[Xem Lịch sử Thay đổi (Changelog)](CHANGELOG.md) | [Xem Lộ trình Phát triển (Roadmap)](ROADMAP.md) | [Xem Quy trình Làm việc (Workflow)](WORKFLOW.md) | [Ghi chú Kỹ thuật](TECHNICAL_NOTES.md)**

---

Một công cụ desktop được xây dựng bằng Python và CustomTkinter, chuyên dụng cho việc bóc tách và cấu trúc hóa nội dung (văn bản và hình ảnh) từ các file PDF và EPUB một cách thông minh.



## Luồng làm việc Cốt lõi

Ứng dụng được thiết kế để tự động hóa quá trình lấy dữ liệu từ các file ebook phức tạp thông qua một quy trình 5 bước:

1.  **Chọn File:** Người dùng chọn một file `.pdf` hoặc `.epub` từ máy tính.
2.  **Phân tích Thông minh:** Chương trình tự động đọc **Mục lục (Table of Contents)** được tích hợp sẵn trong file (Bookmarks đối với PDF, ToC đối với EPUB) để xác định chính xác ranh giới và tiêu đề của từng chương/bài viết.
3.  **Bóc tách Toàn diện:** Với mỗi chương đã xác định, ứng dụng sẽ quét và trích xuất tuần tự toàn bộ nội dung, bao gồm các khối **văn bản** và các file **hình ảnh**. Hình ảnh được tạm thời lưu vào một thư mục đệm.
4.  **Xác minh Trực quan:** Toàn bộ cấu trúc đã bóc tách (tiêu đề chương, văn bản, và "mỏ neo" đại diện cho hình ảnh) được hiển thị trên giao diện chính để người dùng kiểm tra và xác nhận tính toàn vẹn của dữ liệu.
5.  **Lưu trữ có Tổ chức:** Người dùng có thể lưu toàn bộ kết quả ra máy tính. Ứng dụng sẽ tự động tạo một thư mục gốc mang tên sách, và bên trong là các thư mục con được đặt tên theo từng chương. Mỗi thư mục chương chứa một file `content.txt` với toàn bộ văn bản và các file hình ảnh tương ứng.

---
## Cấu trúc Dự án

Dự án tuân thủ nguyên tắc Tách bạch Trách nhiệm, với logic và giao diện được phân chia rõ ràng.


``` javascript
src/extract_app/
│
├── core/                       # Chứa các logic nghiệp vụ nền
│   ├── pdf_parser.py           # Logic trích xuất và phân tích file PDF.
│   ├── epub_parser.py          # Logic trích xuất và phân tích file EPUB.
│   └── storage_handler.py      # Logic lưu file và thư mục.
│
├── modules/                    # Chứa các module giao diện người dùng
│   ├── main_window.py          # Cửa sổ chính và các thành phần giao diện.
│   └── ...                     # (Các file UI placeholder cho tương lai)
│
└── shared/                     # (Dự phòng cho các thành phần dùng chung)
└── ...

```

---
## Hướng dẫn Cài đặt (Dành cho Lập trình viên)

* **Yêu cầu Hệ thống:**
    * Python 3.9+
* **Các bước:**
    1.  Clone repository: `git clone [URL]`
    2.  Tạo môi trường ảo: `python -m venv venv` và kích hoạt nó.
    3.  Cài đặt các thư viện cần thiết: `pip install -r requirements.txt`
    4.  Chạy ứng dụng: `python run.py`
