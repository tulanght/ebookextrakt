# SPEC: Search UI — Tab "Tìm Kiếm Sách" trong E-Extract

**Mục đích:** Cho phép user tìm kiếm nội dung từ 91k+ articles đã index qua FTS5,
trực tiếp trong app thay vì phải dùng CLI `scripts/search.py`.

**Thực hiện bởi:** Antigravity
**Không cần hỏi lại:** Architecture và UI pattern đã chốt bên dưới.
**Phụ thuộc:** `db_manager.search_content()` đã tồn tại ở `database.py:904` — không cần thêm method.

---

## Tổng quan thay đổi (4 file)

| File | Thay đổi |
|------|----------|
| `src/extract_app/modules/ui/search_view.py` | **TẠO MỚI** — View chính |
| `src/extract_app/modules/ui/sidebar.py` | **SỬA** — Thêm nav item |
| `src/extract_app/modules/main_window.py` | **SỬA** — Khởi tạo + register view |
| *(không đụng gì khác)* | — |

---

## 1. `search_view.py` — View chính

### Layout tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│  SEARCH BAR ROW                                                 │
│  [🔍 Tìm trong 91,521 articles...      ] [Category ▼] [Tìm]   │
├────────────────────────────────┬────────────────────────────────┤
│  RESULTS PANEL (scroll)        │  DETAIL PANEL                  │
│                                │                                │
│  [Card kết quả 1]              │  📚 Tên sách                  │
│  [Card kết quả 2]              │  Chapter › Section            │
│  [Card kết quả 3]              │  [animal]                     │
│  ...                           │                                │
│                                │  ─────────────────────────    │
│                                │  Nội dung đầy đủ (scroll)     │
│                                │                                │
│                                │  [📋 Copy đoạn văn]           │
└────────────────────────────────┴────────────────────────────────┘
```

**Tỷ lệ cột:** Left panel = weight 2, Right panel = weight 3 (tương tự `keyword_plan_view.py`).

### Constructor signature

```python
class SearchView(ctk.CTkFrame):
    def __init__(self, master, db_manager, **kwargs):
        # Chỉ cần db_manager — không cần settings_manager hay translation_service
```

### Search bar row

- `ctk.CTkEntry` — placeholder `"🔍 Tìm trong 91,521 articles..."`, `fg_color=Colors.BG_INPUT`, height=40
- Bind `<Return>` → trigger search (user gõ Enter là tìm ngay, không cần click button)
- `ctk.CTkOptionMenu` — options: `["Tất cả", "animal", "plant", "overlap"]`, width=120
  - Map "Tất cả" → `None` khi gọi `search_content()`
- `ctk.CTkButton` — text `"Tìm"`, `fg_color=Colors.PRIMARY`, width=80

### Left panel — Result cards

```python
self.results_scroll = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
```

**Khi chưa tìm:** Label muted `"Nhập từ khóa để tìm trong thư viện ebooks."`

**Khi đang tìm:** Hiện loading spinner text `"Đang tìm..."` (label đơn giản, không cần overlay)

**Khi có kết quả:** Render danh sách cards. Mỗi card:

```python
def _create_result_card(self, item: dict, index: int) -> ctk.CTkFrame:
    """
    item keys: book_title, chapter_title, section_title, site_category,
               word_count, snippet, passage, rank
    """
```

Card layout (compact, height ~80px):
```
┌─────────────────────────────────────────────┐
│ 📚 Tên sách (Fonts.BODY_BOLD, TEXT_PRIMARY) │
│ Chapter › Section     [animal] badge        │
│ "...snippet ngắn..." (TEXT_MUTED, TINY)     │
└─────────────────────────────────────────────┘
```

- Badge `site_category`: màu `Colors.SUCCESS` cho animal, `Colors.WARNING` cho plant, `Colors.PRIMARY` cho overlap
- Click vào card → hiện detail ở right panel
- Active card: `border_color=Colors.PRIMARY`, inactive: `Colors.BORDER`

**Khi không có kết quả:** Label `"Không tìm thấy kết quả cho '[query]'."`, `Colors.TEXT_MUTED`

### Right panel — Detail view

**Khi chưa chọn card:** Label `"Chọn một kết quả để xem nội dung đầy đủ."` (căn giữa, muted)

**Khi đã chọn:**
- Header: tên sách (`Fonts.H3`), breadcrumb `"Chapter › Section"` (`Colors.TEXT_MUTED`)
- Badge category
- Separator line (`Colors.BORDER`)
- `ctk.CTkTextbox` — full passage text, readonly (`state="disabled"`), `fg_color=Colors.BG_INPUT`, `font=Fonts.CODE`, wrap="word", fill both axes
- Button row (bottom): `[📋 Copy đoạn văn]`
  - Copy action: `self.clipboard_clear(); self.clipboard_append(passage_text)`
  - Sau copy: đổi text button thành `"✅ Đã copy"` rồi reset sau 2 giây (`self.after(2000, reset_btn)`)

### Search logic — chạy trong thread

```python
def _on_search(self):
    query = self.entry_search.get().strip()
    if not query:
        return

    category_label = self.option_category.get()
    category = None if category_label == "Tất cả" else category_label

    # Clear results, show loading
    self._clear_results()
    self._show_loading()

    def worker():
        try:
            results = self.db_manager.search_content(
                query=query,
                site_category=category,
                limit=20,        # hiện 20 kết quả
                min_words=50
            )
            self.after(0, lambda: self._render_results(results, query))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))

    threading.Thread(target=worker, daemon=True).start()
```

**Lưu ý:** Dùng `self.after(0, ...)` để update UI từ thread — đúng pattern của codebase hiện tại.

---

## 2. `sidebar.py` — Thêm nav item

**Vị trí:** Thêm vào `NAV_ITEMS` list, sau `"Từ Khoá"`, trước `"Cài đặt"`:

```python
NAV_ITEMS = [
    ("🏠", "Dashboard",     "dashboard"),
    ("📚", "Thư viện",      "library"),
    ("🚀", "Publishing",    "publish"),
    ("🎯", "Từ Khoá",       "keyword"),
    ("🔍", "Tìm Kiếm",      "search"),   # ← THÊM DÒNG NÀY
    ("⚙️", "Cài đặt",      "settings"),
]
```

---

## 3. `main_window.py` — Khởi tạo và register

### Import (thêm vào block imports đã có):

```python
from .ui.search_view import SearchView
```

### Khởi tạo view (thêm vào `_init_components()`, sau `keyword_plan_view`):

```python
self.search_view = SearchView(
    self.content_area,
    db_manager=self.db_manager,
)
```

### `_show_view()` — thêm 2 chỗ:

**Trong phần "Hide all":**
```python
self.search_view.grid_forget()
```

**Trong phần "Show selected":**
```python
elif view_name == "search":
    self.search_view.grid(row=0, column=0, sticky="nsew")
```

### `_on_navigate()` — thêm handler:

```python
elif view_name == "search":
    self._show_view("search")
```

---

## Acceptance Criteria

- [ ] Sidebar hiện nav item "🔍 Tìm Kiếm" giữa "Từ Khoá" và "Cài đặt"
- [ ] Gõ query + Enter (hoặc click Tìm) → kết quả xuất hiện trong left panel
- [ ] Kết quả chạy trong background thread — UI không đơ trong lúc tìm
- [ ] Filter category hoạt động: chọn "plant" chỉ trả plant books
- [ ] Click card → right panel hiện full passage text
- [ ] Nút "📋 Copy đoạn văn" copy text vào clipboard, flash "✅ Đã copy" 2 giây
- [ ] Không tìm thấy → hiện thông báo rõ ràng (không crash, không để trống)
- [ ] Active card được highlight border PRIMARY
- [ ] Không đụng code của bất kỳ view nào khác

---

## Không cần làm (out of scope)

- Không cần save search history
- Không cần pagination (limit=20 đủ dùng)
- Không cần highlight từ khóa trong passage (snippet đã có `<b>` tags — bỏ qua hoặc strip)
- Không cần "Export kết quả"
- Không cần thêm method mới vào `database.py` — `search_content()` đã đủ
