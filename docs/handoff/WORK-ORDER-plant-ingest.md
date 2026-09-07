# WORK ORDER — Nạp kho Thực vật vào extract.db

**Người giao:** Claude (giám sát) · **Người làm:** Antigravity CLI (`agy`) · **Ngày:** 2026-08-30
**Nghiệm thu:** `python .claude/verify/check.py` — Claude chạy độc lập, KHÔNG đọc báo cáo của script.

---

## 0. LUẬT TỐI THƯỢNG — đọc trước, vi phạm là hỏng không cứu được

1. **KHÔNG `DELETE` / `DROP` / `TRUNCATE`** trên `user_data/extract.db`. "Dọn" ở đây là `UPDATE`, làm sạch nội dung — **không phải xóa bản ghi**. Số article trước và sau phải bằng nhau: **95.628 → 95.628**.
2. **KHÔNG sửa, KHÔNG xóa file `content.txt` trên đĩa.** Thẻ `[Image Anchor: ...]` trong đó là dữ liệu vị trí ảnh, phục vụ dịch sách. Mất là mất vĩnh viễn. `content.txt` là MASTER, chỉ đọc.
3. **KHÔNG đổi chữ ký `DatabaseManager.fts_search_raw()`** và **KHÔNG đổi CLI của `scripts/research.py`** (`--plan` / `--backend` / `--force`). Ba app ở ba repo khác đang phụ thuộc. Đổi = vỡ hợp đồng.
4. **KHÔNG chạy `rebuild_fts_index()`.** Lệnh rebuild đọc lại TOÀN BỘ bảng `articles`, kéo 10.784 container `is_leaf=0` vào index. Trigger `articles_fts_update` đã tự đồng bộ khi UPDATE, không cần làm gì thêm.
5. **Backup đã có** tại `D:\_backup\extract.db.20260830_075026.bak` (sha256 `7ff6dda4...`). Trước mỗi việc GHI vào DB (việc 3, 4), tạo thêm một backup mới.

### DỪNG NGAY và ghi vào `docs/handoff/ANTIGRAVITY-ASK.md` nếu gặp:

- Cần chạy bất kỳ `DELETE` / `DROP` / `TRUNCATE` nào
- Cần sửa hoặc xóa file `content.txt`
- Số cuốn trùng phát hiện được **ngoài khoảng 100–150** (dự kiến 127)
- Cần đổi chữ ký `fts_search_raw()` hoặc CLI `research.py`
- Số article sau import lệch quá 10% so với dự kiến
- `python .claude/verify/check.py` báo **FAIL** (khác với TODO)

---

## 1. Bối cảnh — số liệu đã đo 2026-08-30

| Hạng mục | Số liệu |
|---|---|
| `extract.db` | 573 MB · 1.264 sách · 95.628 article (84.844 leaf) · FTS5 đủ 95.628 |
| Kho vườn `D:\Garden Home and Plants` | **234 thư mục sách** · 38.283 `content.txt` · **0** `.md` · **0** `metadata.json` |
| Trùng với sách đã có trong DB | **127 cuốn** (theo title chuẩn hóa) |
| Mới hoàn toàn | **107 cuốn** |
| `site_category` | animal 303 · plant 63 · overlap 33 · **NULL 861** |
| Article dính `[Image Anchor:` trong DB | **886** (tất cả thuộc sách `animal`) |
| Cặp sách trùng title có sẵn | **121** (ô nhiễm cũ, KHÔNG thuộc phạm vi đợt này) |

**Mục tiêu duy nhất:** app sản xuất video ngắn của dự án Thực vật truy xuất được kho sách vườn. Không dựng Research UI, không làm portable DB, không bật QMD/Jina.

---

## 2. TÁM VIỆC

### Việc 5 — An ninh (LÀM TRƯỚC, độc lập)

`src/extract_app/core/database.py:1111` hard-code `JINA_API_KEY`.

- Rút ra `.env`, đọc qua `os.getenv('JINA_API_KEY')`
- Key còn nằm trong `dist/E-Extract/_internal/src/extract_app/core/database.py` → xóa thư mục `dist/`
- Thêm `dist/` và `vr-cuongjsl-*.json` vào `.gitignore`
- **Báo user tự revoke key** trên dashboard Jina — agy không tự làm được

### Việc 1 — Importer nhận `content.txt`

`scripts/bulk_import_extracted.py:69` dùng `rglob("content.md")`. Kho vườn có **0** file `.md` → hàm trả `return 0, 0` (status skip) → **import 0 article, không báo lỗi**.

- Sửa để nhận cả `content.md` và `content.txt`
- Nếu một cuốn có **cả hai**, ưu tiên `.md`
- `parse_content_md()` hiện parse YAML frontmatter; `.txt` không có frontmatter → phải xử lý nhánh không-frontmatter mà không crash

### Việc 2 — Ngưỡng bỏ file vụn, khai báo MỘT chỗ

- Ngưỡng: **400 byte**. **KHÔNG được nâng** — bài 150 từ vẫn có giá trị cho video ngắn.
- Hiện `tools/markdown_exporter.py` dùng ngưỡng khác (`< 100` ký tự). **Phải thống nhất**: khai báo hằng số ở MỘT chỗ dùng chung, cả importer lẫn exporter cùng đọc.
- Không thống nhất thì việc 8 (đối soát) sẽ báo lệch mãi mãi và thành vô dụng.

### Việc 3 — Làm sạch `[Image Anchor:` trong DB

- Regex: `\[Image Anchor:[^\]]*\]`
- Áp dụng **khi import** (article mới) **và** cho 886 article cũ đang dính
- Thao tác: `UPDATE articles SET content_text = <đã strip>, word_count = <tính lại>`
- **TUYỆT ĐỐI KHÔNG `DELETE`** — xem luật 1
- Trigger tự đồng bộ FTS5. **Không** gọi `rebuild_fts_index()`.
- **Không** đụng file `content.txt` trên đĩa

### Việc 6 — Dedup theo title chuẩn hóa (MỚI — chặn 127 bản trùng)

`book_already_imported()` (dòng 55-62) so `source_path = str(book_folder)`. Nhưng **0/234** thư mục kho vườn khớp: DB lưu đường dẫn file gốc (`D:\Ebooks\Biology\Botany and Plants\X.epub`), còn importer đưa vào đường dẫn thư mục đã extract (`D:\Garden Home and Plants\X`). Không bao giờ bằng nhau → 127 cuốn bị import lần hai.

- Đổi sang so **title đã chuẩn hóa** (lowercase, bỏ khoảng trắng / gạch nối / nháy)
- Cuốn **đã có** → **CẬP NHẬT tại chỗ**: gán `site_category='plant'`, bổ sung article còn thiếu. **KHÔNG tạo bản ghi book mới.**
- Cuốn **mới** → thêm bình thường
- Phải **idempotent**: chạy lại lần hai không được nhân đôi bất cứ gì

### Việc 4 — Gán `site_category='plant'`

- Cho toàn bộ 234 cuốn kho vườn (cả 127 cập nhật lẫn 107 mới)
- Bỏ bước này là hỏng hết: mọi consumer lọc cứng theo cột này, để `NULL` thì dữ liệu vô hình dù đã nằm trong DB

### Việc 7 — Sinh `content.md` cho kho vườn

`tools/markdown_exporter.py` đã làm gần đủ: nhận `--dir`, duyệt `content.txt`, ghi `content.md` nằm cạnh (không đụng file gốc), sinh YAML frontmatter + heading `#`.

- **Thiếu duy nhất:** trong `process_file()`, biến `markdown_body = content` — chưa strip `[Image Anchor:`. Thêm strip.
- Thống nhất ngưỡng theo việc 2
- Chạy: `python tools/markdown_exporter.py --dir "D:\Garden Home and Plants"`
- Kết quả đúng: `content.txt` **CÒN** thẻ (master nguyên vẹn), `content.md` **HẾT** thẻ

### Việc 8 — Lệnh đối soát chống trôi lệch

Kho động vật đang trôi lệch **18%** mà không ai biết: 120.636 `content.txt` nhưng chỉ 98.913 `content.md`, và QMD chỉ index 95.021. Cùng một lớp lỗi đã cắn dự án 3 lần.

- Viết `scripts/reconcile_corpus.py --dir <root>` in ra và so 4 con số: `content.txt` trên đĩa · `content.md` trên đĩa · article trong DB · document trong QMD index
- Trừ đi số file bị ngưỡng 400 byte loại
- Lệch → **exit ≠ 0**, in rõ lệch ở đâu

---

## 3. THỨ TỰ THI CÔNG

```
Việc 5 (an ninh, độc lập)
  → Việc 1 + 2 + 3 + 6   (sửa importer, CHƯA ghi DB)
  → Việc 7               (exporter)
  → Việc 8               (đối soát)
  → CHẠY THỬ ĐÚNG 1 CUỐN → check.py → báo Claude nghiệm thu
  → Chỉ khi Claude duyệt: import toàn bộ 234 cuốn + việc 4
  → check.py đầy đủ
```

**Chạy thử 1 cuốn trước khi import 234 cuốn.** Sai ở khâu strip hoặc `site_category` mà phát hiện sau khi nạp hết thì phải khôi phục backup và làm lại từ đầu.

---

## 4. NGHIỆM THU

Sau mỗi việc: `python .claude/verify/check.py --fast`
Cuối cùng: `python .claude/verify/check.py` (đầy đủ, có quét đĩa)

**FAIL** = bất biến bị phá → dừng, khôi phục backup, báo Claude.
**TODO** = mục tiêu chưa đạt → bình thường khi chưa làm xong.

Số kỳ vọng khi hoàn tất:

| Hạng mục | Trước | Sau |
|---|---|---|
| books | 1.264 | **~1.371** (chỉ +107; 127 cập nhật tại chỗ) |
| plant books | 63 | **~297** |
| plant article (leaf) | 11.188 | **~36.000** |
| `[Image Anchor:` trong DB | 886 | **0** |
| `[Image Anchor:` trong `content.txt` | có | **vẫn có** ← master nguyên vẹn |
| `[Image Anchor:` trong `content.md` | — | **0** |
| article tổng | 95.628 | **≥ 95.628**, không bao giờ giảm |
| cặp trùng title | 121 | **≤ 121**, không được tăng |

---

## 5. RÀNG BUỘC KỸ THUẬT (theo AGENTS.md)

- Kích hoạt venv trước mọi lệnh Python: `.\venv\Scripts\activate`
- Nhánh `feature/*`, không commit vào `main`
- Conventional commits, atomic
- Header block Python đầu mỗi file
- Cập nhật `CHANGELOG.md` + `ROADMAP.md` trước khi đóng task
