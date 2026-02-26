# Ghi chú Kỹ thuật & Quyết định Kiến trúc
# version: 1.0
# last-updated: 2025-09-20
# description: Ghi lại các thách thức kỹ thuật và quyết định kiến trúc cốt lõi trong phiên bản alpha đầu tiên.

Tài liệu này ghi lại những vấn đề kỹ thuật hóc búa đã gặp phải và các quyết định cuối cùng đã được đưa ra để giải quyết chúng. Đây là tài liệu bắt buộc phải đọc để hiểu lý do tại sao các thành phần cốt lõi của ứng dụng được xây dựng theo cách hiện tại.

---

### **1. Thách thức Cốt lõi: Phân tích sự Thiếu nhất quán của File EPUB**

Đây là trở ngại lớn nhất và kéo dài nhất trong giai đoạn phát triển đầu tiên.

* **Bối cảnh:** Các file EPUB từ nhiều nguồn khác nhau có cấu trúc Mục lục (ToC) và HTML bên trong cực kỳ đa dạng và thường không tuân theo một tiêu chuẩn duy nhất.
* **Các Thất bại Ban đầu (v2.x - v11.x):**
    * Các thuật toán ban đầu (dựa trên `find_all` đơn giản hoặc đệ quy cơ bản) đã thất bại vì chúng đưa ra những giả định sai lầm:
        1.  Giả định rằng ToC chỉ chứa các đối tượng `Link` và `tuple`, nhưng thực tế nó còn chứa các đối tượng `Section` phức tạp.
        2.  Giả định rằng nội dung text/image nằm ở các thẻ con trực tiếp của `<body>`, nhưng thực tế chúng thường được lồng sâu vào trong nhiều lớp thẻ `<div>`.
        3.  Giả định rằng đường dẫn hình ảnh (`src`) trong thẻ `<img>` là đường dẫn tuyệt đối, nhưng thực tế chúng hầu hết là **đường dẫn tương đối** (`../images/...`).

* **Quyết định Kiến trúc (v12.0 trở đi):**
    * **Bắt buộc phải duyệt ToC một cách đệ quy sâu:** Thuật toán cuối cùng được thiết kế để có thể "đi" vào mọi loại đối tượng có thể lặp lại (`__iter__`) trong ToC, đảm bảo không bỏ sót bất kỳ mục con nào, dù chúng là `Link`, `tuple`, hay `Section`.
    * **Bắt buộc phải giải quyết đường dẫn tương đối:** Logic xử lý hình ảnh được bổ sung thêm một bước quan trọng: sử dụng `os.path.normpath` để giải quyết các đường dẫn tương đối (`../`) thành một đường dẫn tuyệt đối bên trong cấu trúc file EPUB trước khi tìm kiếm. Đây là chìa khóa để khắc phục lỗi không tìm thấy ảnh.
    * **Sử dụng `find_all` để quét nội dung:** Thay vì các thuật toán duyệt cây phức tạp, giải pháp cuối cùng và đáng tin cậy nhất là sử dụng `soup.body.find_all(...)` để lấy ra một danh sách "phẳng" và tuần tự của tất cả các thẻ nội dung quan trọng.

---

### **2. Vấn đề Hiệu năng Giao diện & Trải nghiệm Người dùng**

* **Triệu chứng:** Khi xử lý các file có hàng trăm hình ảnh, ứng dụng bị treo cứng (đơ), và khu vực hiển thị kết quả trắng xóa (`_tkinter.TclError: row out of bounds`).
* **Nguyên nhân gốc:** Giao diện `CustomTkinter` bị quá tải khi phải khởi tạo và render hàng trăm widget hình ảnh cùng một lúc, dẫn đến cạn kiệt tài nguyên và crash.
* **Quyết định Kiến trúc:**
    * **Từ bỏ việc hiển thị ảnh thật:** Chúng ta đã quyết định rằng vai trò của giao diện là một công cụ **xác minh dữ liệu**, không phải một trình đọc ebook.
    * **Triển khai Hệ thống "Image Anchor":** Đây là giải pháp cốt lõi. Thay vì tải dữ liệu ảnh vào bộ nhớ và hiển thị, parser sẽ lưu file ảnh ra một thư mục `/temp` và chỉ trả về **đường dẫn (anchor)**. Giao diện chỉ có nhiệm vụ hiển thị chuỗi đường dẫn này. Quyết định này đã giải quyết triệt để vấn đề hiệu năng.

---

### **3. Vấn đề Tương thích Môi trường & Thư viện**

* **Triệu chứng:** Chức năng "Lưu kết quả" liên tục bị crash với lỗi `_tkinter.TclError: Unspecified error` khi gọi `filedialog.askdirectory`.
* **Quá trình Điều tra:** Lỗi được xác định là một sự xung đột sâu giữa phiên bản Python, thư viện `tkinter` gốc, `customtkinter`, và cách hệ điều hành Windows quản lý các hộp thoại. Các giải pháp thông thường (chỉ định `parent`, gọi `ctk.filedialog`) đều không hiệu quả.
* **Quyết định Kiến trúc (Workaround):**
    * **Loại bỏ hoàn toàn `filedialog.askdirectory`:** Chấp nhận rằng thành phần này không ổn định trong môi trường của chúng ta.
    * **Thay thế bằng Ô nhập liệu:** Triển khai một giải pháp thay thế: người dùng sẽ tự sao chép và dán đường dẫn thư mục muốn lưu vào một ô `CTkEntry`. Quyết định này ưu tiên sự **ổn định** của ứng dụng hơn là sự tiện lợi của người dùng.