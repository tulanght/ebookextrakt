# SPEC: Bulk Import — D:\Extracted-EBOOKS → SQLite DB

**Mục đích:** Import 400 cuốn từ filesystem vào DB để FTS5 search hoạt động.  
**Thực hiện bởi:** Antigravity  
**Phụ thuộc:** SPEC_fts5_search.md Task 0 (backfill site_category) đã DONE  
**Không cần hỏi lại:** Architecture đã chốt bên dưới.

---

## Bối cảnh

E-Extract app extract và lưu DB *đồng thời*. Tuy nhiên 400/416 cuốn trong
`D:\Extracted-EBOOKS` được extract bằng script riêng — chỉ có trên filesystem,
**không có trong DB**. FTS5 search vì vậy chỉ hoạt động trên 6 cuốn test.

**Scope thực tế:**
- 95,315 `content.md` files cần đọc
- 400 books cần import (loại 21 cuốn `off`)
- Depth 2–8 (đa số depth 3–4)

---

## Script: `scripts/bulk_import_extracted.py`

### Interface CLI

```bash
# Import toàn bộ (dry run trước)
python scripts/bulk_import_extracted.py --dry-run

# Import thật
python scripts/bulk_import_extracted.py

# Import 1 cuốn cụ thể (debug)
python scripts/bulk_import_extracted.py --book "Cheetah"

# Xem progress
python scripts/bulk_import_extracted.py --verbose
```

### Logic tổng quan

```
1. Đọc _classification.json → danh sách 400 folders (skip category='off')
2. for each book_folder:
     if book đã có trong DB (match source_path) → skip
     Collect tất cả content.md trong folder
     Xây dựng chapter map từ content.md frontmatter
     Insert: book → chapters → articles (1 transaction/book)
3. Sau khi xong → rebuild FTS5 index 1 lần
4. Report: X books imported, Y articles indexed, Z skipped
```

---

## Mapping: Filesystem → DB

### Source path convention (QUAN TRỌNG)

`books.source_path` phải set = **đường dẫn folder** (không phải file .epub/.pdf gốc):

```
books.source_path = "D:\\Extracted-EBOOKS\\Cheetah"
```

Lý do: `backfill_site_category.py` match theo folder name → `source_path` phải
nhất quán để site_category lookup hoạt động cho các books import sau này.

### Book record

Lấy từ frontmatter của **bất kỳ** `content.md` nào trong folder (dùng file đầu tiên tìm thấy):

```python
book = {
    "title":        frontmatter["book_title"],
    "author":       frontmatter["author"],        # có thể empty/sai — OK
    "published_year": frontmatter["published_year"],
    "source_path":  str(book_folder),             # D:\Extracted-EBOOKS\<folder>
    "site_category": frontmatter["site_category"] # đã backfill: animal|plant|overlap
}
```

Nếu `site_category` không có trong frontmatter → fallback lookup từ `_classification.json`.

### Chapter records

Một chapter = **second-level subfolder** (depth 2 relative to book folder).

```
D:\Extracted-EBOOKS\Cheetah\
    01 - Imprint page\          ← chapter 1
    02 - Acknowledgements\      ← chapter 2
    05 - 1 The cheetah in history\  ← chapter 5
```

```python
chapter = {
    "book_id":     <book_id vừa insert>,
    "title":       frontmatter["chapter_title"] hoặc folder_name nếu empty,
    "order_index": int(folder_name[:2])  # "05 - ..." → 5
}
```

### Article records

Mỗi `content.md` = 1 article. **Đọc toàn bộ file**, tách frontmatter và body:

```python
article = {
    "chapter_id":    <chapter_id tương ứng>,
    "subtitle":      frontmatter["article_title"],
    "content_text":  body,           # text sau dấu '---' thứ 2, bỏ header markdown
    "order_index":   frontmatter["section_index"] * 1000 + depth_bonus,
    "is_leaf":       <xem bên dưới>,
    "word_count":    frontmatter["word_count"]   # đã có, không cần tính lại
}
```

**Xác định is_leaf:**
```python
# Leaf = folder chứa content.md này không có subfolder nào có content.md
def is_leaf(content_md_path: Path) -> bool:
    parent = content_md_path.parent
    return not any(
        (child / "content.md").exists()
        for child in parent.iterdir()
        if child.is_dir()
    )
```

**Tách body từ content.md:**
```python
def parse_content_md(filepath: Path) -> tuple[dict, str]:
    """Returns (frontmatter_dict, body_text)"""
    text = filepath.read_text(encoding='utf-8', errors='replace')
    parts = text.split('---', 2)
    # parts[0] = '' (trước ---)
    # parts[1] = YAML frontmatter
    # parts[2] = body content
    if len(parts) < 3:
        return {}, text
    import yaml
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()
    return fm, body
```

**Lọc noise trong body:** Bỏ dòng cuối `> **Nguồn:**...` (footer tự động thêm bởi extractor):
```python
body = re.sub(r'\n+> \*\*Nguồn:\*\*.*$', '', body, flags=re.MULTILINE).strip()
```

---

## Chapter assignment — xử lý depth > 2

Vấn đề: `content.md` ở depth 4, 5, 6... thuộc chapter nào?

**Rule:** Chapter = **second-level folder** relative to book root. Mọi `content.md` ở depth sâu hơn đều thuộc chapter của ancestor depth-2 của nó.

```python
def get_chapter_folder(content_md_path: Path, book_root: Path) -> Path:
    """Trả về second-level subfolder (chapter) chứa file này."""
    relative = content_md_path.relative_to(book_root)
    # relative.parts[0] = chapter folder name
    # relative.parts[1:] = section/subsection/...
    return book_root / relative.parts[0]
```

---

## Performance

95,315 files × parse YAML + insert DB = có thể chậm nếu không tối ưu.

**Bắt buộc:**
- Dùng `save_book_batch()` của `DatabaseManager` (single transaction/book) — **không** insert từng article riêng lẻ
- Đọc và parse toàn bộ content.md của 1 book → build structured_content list → `save_book_batch()` 1 lần
- Tắt WAL sync trong lúc import: `PRAGMA synchronous = OFF` (bật lại sau)

**Target:** 400 books trong < 5 phút.

**Cách build structured_content cho `save_book_batch()`:**

`save_book_batch()` nhận `structured_content: list` theo format:
```python
[
    {   # chapter node
        "title": "1 The cheetah in history",
        "content": [],          # chapter intro thường không có content
        "children": [
            {   # section node
                "title": "1THE CHEETAH IN HISTORY",
                "content": [("text", body_text)],
                "children": []
            },
            ...
        ]
    },
    ...
]
```

Build cây này bằng cách group content.md files theo chapter folder, sau đó
sort theo `section_index` trong frontmatter.

---

## Skip logic (idempotent)

```python
def book_already_imported(db: DatabaseManager, book_folder: Path) -> bool:
    """Check bằng source_path."""
    conn = db._get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM books WHERE source_path = ?", (str(book_folder),))
    result = c.fetchone()
    conn.close()
    return result is not None
```

---

## FTS5 rebuild sau import

Sau khi tất cả books đã import xong:

```python
print("Rebuilding FTS5 index...")
count = db.rebuild_fts_index()
print(f"FTS5: {count:,} articles indexed.")
```

**Không** dựa vào triggers cho bulk import (triggers chạy per-insert = chậm).
`rebuild_fts_index()` nhanh hơn nhiều cho lần đầu.

---

## Output / Progress

```
[1/400] Cheetah (animal) — 27 chapters, 145 articles ... OK
[2/400] How Snakes Work (animal) — 16 chapters, 89 articles ... OK
[3/400] Cacti and Succulents (plant) — 8 chapters, 52 articles ... OK
...
[47/400] The Earth Transformed (off) — SKIPPED (off-topic)
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Import complete
  Books imported : 400
  Books skipped  : 21 (off) + 0 (already in DB)
  Total articles : 94,821
  FTS5 indexed   : 67,443 (is_leaf only)
  Duration       : 3m 42s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Sau import — verify với search.py

```bash
# Phải trả >= 5 kết quả
python scripts/search.py "king cobra venom" --limit 5

# Phải trả kết quả từ plant books
python scripts/search.py "cactus water storage" --category plant --limit 3

# Phải trả site_category: animal
python scripts/search.py "elephant herd matriarch" --category animal --limit 3

# Không được trả kết quả từ plant/off
python scripts/search.py "snake venom" --category animal --limit 5
# → verify: tất cả results có site_category=animal
```

---

## Acceptance Criteria

- [ ] `python scripts/bulk_import_extracted.py --dry-run` chạy không crash, in danh sách 400 books
- [ ] `python scripts/bulk_import_extracted.py` import xong trong < 10 phút
- [ ] `SELECT COUNT(*) FROM books` → ≥ 400
- [ ] `SELECT site_category, COUNT(*) FROM books GROUP BY site_category` → có `animal`, `plant`, `overlap`
- [ ] `SELECT COUNT(*) FROM articles_fts` → > 50,000
- [ ] `python scripts/search.py "cactus water storage" --category plant --limit 3` → ≥ 1 kết quả
- [ ] `python scripts/search.py "king cobra" --limit 5` → ≥ 3 kết quả
- [ ] Import idempotent: chạy lại lần 2 → số books không tăng

---

## Không cần làm (scope của spec này)

- KHÔNG re-extract bất kỳ file nào (chỉ đọc content.md đã có)
- KHÔNG dịch hay generate content
- KHÔNG thay đổi `database.py` hay `search.py` (đã done ở SPEC_fts5_search.md)
- KHÔNG import books có `category=off` trong `_classification.json`
