# SPEC: FTS5 Search Layer — Context Retrieval for Article Pipeline

**Mục đích:** Cho phép Antigravity tra cứu ngữ cảnh từ 416 cuốn ebook khi viết bài.  
**Thực hiện bởi:** Antigravity  
**Phụ thuộc:** SPEC_cleanup_and_classify.md đã DONE  
**Không cần hỏi lại:** Architecture và interface đã chốt bên dưới.

---

## Tổng quan

Thêm 3 thứ vào E-Extract:

1. **`site_category` field** backfill vào tất cả `content.md` — prerequisite cho search filter
2. **FTS5 index** trong `database.py` — cho phép tìm kiếm full-text trên toàn bộ `articles.content_text`
3. **CLI script** `scripts/search.py` — interface để Antigravity gọi khi viết bài

```
python scripts/search.py "king cobra venom mechanism" --limit 5
```

→ Trả về JSON với top passages + metadata (book, chapter, word count)

---

## ⚠️ Metadata Audit — Vấn đề phát hiện khi đọc content.md

**Đã kiểm tra thực tế 4 files từ 3 cuốn khác nhau. Phát hiện:**

### Vấn đề 1: `category` và `folder_category` dùng nhầm — không ai = site-category

| File | `category` | `folder_category` |
|------|-----------|-------------------|
| How Snakes Work | `Reptilia` (taxonomic class) | `''` (trống) |
| Marine Mammals | `Insecta` **(sai loài!)** | `Mammalia` (taxonomic family) |
| Cheetah | `Felidae` (family) | `Felidae` (trùng, redundant) |

**Hậu quả:** Search filter `--category animal` sẽ không hoạt động vì không có field nào chứa `animal`/`plant`/`overlap`. Cần thêm field `site_category` riêng biệt.

### Vấn đề 2: `author` bị parse sai từ tên file

- `Cheetah`: `author: z-lib.org` ← lấy nhầm nguồn tải
- `Marine Mammals`: `author: '2021'` ← lấy nhầm năm xuất bản

**Hậu quả:** Nhỏ, không block pipeline, nhưng messy. Fix luôn nếu có thể.

### Vấn đề 3: 6 fields luôn trống trong mọi file đã kiểm tra

```
species_latin, conservation_status, time_period,
ecosystem_type, narrative_type, published_year
```

**Hậu quả:** Dead weight trong frontmatter. Giữ trong schema (sẽ dùng sau) nhưng không cần populate ngay — ghi chú rõ trong code.

---

## Task 0 (Prerequisite): Backfill `site_category` vào tất cả `content.md`

**Đây là task quan trọng nhất — phải làm trước Task 1.**

### Mục tiêu

Thêm field `site_category: animal|plant|overlap|off` vào frontmatter YAML của **mọi** `content.md` trong `D:\Extracted-EBOOKS\`.

Field này tách biệt hoàn toàn khỏi `category`/`folder_category` (taxonomic). Đây là site-level classification dùng cho search filter.

### Nguồn dữ liệu

`D:\Extracted-EBOOKS\_classification.json` — đã có đầy đủ 416 entries từ SPEC trước.

```json
{ "books": [{ "folder": "Cheetah", "category": "animal", ... }] }
```

### Logic backfill

```
for each content.md in D:\Extracted-EBOOKS\**\:
    book_folder = top-level folder name (e.g. "Cheetah")
    lookup _classification.json by folder name
    if found → set site_category = classification.category
    if not found → set site_category = "unclassified"
    update YAML frontmatter in-place
```

### Implementation notes

- Dùng Python + `ruamel.yaml` (preserve formatting) hoặc parse thủ công frontmatter
- **Không** thay đổi nội dung bên dưới `---` — chỉ cập nhật YAML frontmatter
- Nếu `site_category` đã tồn tại trong file → skip (idempotent)
- Script riêng: `scripts/backfill_site_category.py`
- Log kết quả: `X files updated, Y files skipped, Z not found in classification`

### Acceptance

```bash
python scripts/backfill_site_category.py
# → "416 books matched, X files updated"

# Verify
grep "site_category:" "D:/Extracted-EBOOKS/Cheetah/05 - .../content.md"
# → site_category: animal

grep "site_category:" "D:/Extracted-EBOOKS/Cacti and Succulents/.../content.md"
# → site_category: plant
```

---

## Task 1: Thêm FTS5 vào `database.py`

### 1a. FTS5 Virtual Table (trong `_init_db`)

Thêm vào cuối phần `_init_db`, sau tất cả các CREATE TABLE hiện có:

```python
# FTS5 Full-Text Search Index
cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
        content_text,
        subtitle,
        content='articles',
        content_rowid='id',
        tokenize='porter unicode61'
    )
""")

# Trigger: tự động sync khi INSERT article
cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS articles_fts_insert
    AFTER INSERT ON articles BEGIN
        INSERT INTO articles_fts(rowid, content_text, subtitle)
        VALUES (new.id, new.content_text, new.subtitle);
    END
""")

# Trigger: tự động sync khi UPDATE article
cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS articles_fts_update
    AFTER UPDATE ON articles BEGIN
        INSERT INTO articles_fts(articles_fts, rowid, content_text, subtitle)
        VALUES ('delete', old.id, old.content_text, old.subtitle);
        INSERT INTO articles_fts(rowid, content_text, subtitle)
        VALUES (new.id, new.content_text, new.subtitle);
    END
""")

# Trigger: tự động sync khi DELETE article
cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS articles_fts_delete
    BEFORE DELETE ON articles BEGIN
        INSERT INTO articles_fts(articles_fts, rowid, content_text, subtitle)
        VALUES ('delete', old.id, old.content_text, old.subtitle);
    END
""")
```

### 1b. Migration trong `_check_migrations`

**Migration 1 — Thêm `site_category` vào `books` table:**

```python
# Migration: site_category column
cursor.execute("PRAGMA table_info(books)")
book_cols = [row['name'] for row in cursor.fetchall()]
if 'site_category' not in book_cols:
    print("[DB] Migration: Adding site_category to books table.")
    cursor.execute("ALTER TABLE books ADD COLUMN site_category TEXT DEFAULT NULL")
    conn.commit()
    # Note: backfill từ _classification.json thực hiện bởi scripts/backfill_site_category.py
    # sau khi column tồn tại
```

**Migration 2 — FTS5 index:**

Thêm block sau migration site_category:

```python
# Migration: FTS5 index
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles_fts'")
if not cursor.fetchone():
    print("[DB] Migration: Building FTS5 index (first time, may take a moment)...")
    # Tạo virtual table + triggers (copy từ _init_db)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
            content_text, subtitle,
            content='articles', content_rowid='id',
            tokenize='porter unicode61'
        )
    """)
    # ... (tạo 3 triggers như trên)
    
    # Populate từ data hiện có
    cursor.execute("""
        INSERT INTO articles_fts(rowid, content_text, subtitle)
        SELECT id, COALESCE(content_text,''), COALESCE(subtitle,'')
        FROM articles
        WHERE is_leaf = 1
    """)
    conn.commit()
    cursor.execute("SELECT COUNT(*) as c FROM articles_fts")
    count = cursor.fetchone()['c']
    print(f"[DB] FTS5 index built: {count:,} articles indexed.")
```

### 1c. Method `search_content` (thêm vào `DatabaseManager`)

```python
def search_content(
    self,
    query: str,
    site_category: str = None,  # 'animal' | 'plant' | 'overlap' | None (all)
                                # Dùng field site_category, KHÔNG phải category (taxonomic)
    limit: int = 10,
    min_words: int = 50         # Lọc bỏ passages quá ngắn
) -> List[Dict]:
    """
    Full-text search trên toàn bộ articles.content_text.
    
    Filter site_category dùng books.site_category (backfill từ _classification.json),
    KHÔNG phải books.category (taxonomic class — Reptilia, Felidae...).
    
    Returns list of dicts:
    {
        article_id, book_id, book_title, site_category,
        chapter_title, section_title,
        passage,        # đoạn text match (tối đa 500 từ)
        snippet,        # highlight snippet từ FTS5
        rank,           # FTS5 relevance score (thấp hơn = tốt hơn)
        word_count
    }
    """
    conn = self._get_connection()
    try:
        cursor = conn.cursor()
        
        # Build site_category filter (dùng books.site_category, không phải books.category)
        cat_filter = ""
        params = [query]
        if site_category:
            cat_filter = "AND b.site_category = ?"
            params.append(site_category)
        params.append(limit)
        
        cursor.execute(f"""
            SELECT 
                a.id            AS article_id,
                b.id            AS book_id,
                b.title         AS book_title,
                b.site_category AS site_category,
                c.title         AS chapter_title,
                a.subtitle      AS section_title,
                a.content_text  AS passage,
                snippet(articles_fts, 0, '<b>', '</b>', '...', 32) AS snippet,
                articles_fts.rank AS rank,
                a.word_count
            FROM articles_fts
            JOIN articles a ON a.id = articles_fts.rowid
            JOIN chapters c ON c.id = a.chapter_id
            JOIN books b ON b.id = c.book_id
            WHERE articles_fts MATCH ?
              AND a.is_leaf = 1
              AND a.word_count >= {min_words}
              {cat_filter}
            ORDER BY rank
            LIMIT ?
        """, params)
        
        results = []
        for row in cursor.fetchall():
            r = dict(row)
            # Truncate passage to 500 words max
            words = r['passage'].split()
            if len(words) > 500:
                r['passage'] = ' '.join(words[:500]) + '...'
            results.append(r)
        
        return results
    finally:
        conn.close()


def rebuild_fts_index(self) -> int:
    """
    Rebuild toàn bộ FTS5 index từ đầu.
    Dùng sau khi import hàng loạt sách mới.
    Returns: số articles đã index.
    """
    conn = self._get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articles_fts")
        cursor.execute("""
            INSERT INTO articles_fts(rowid, content_text, subtitle)
            SELECT id, COALESCE(content_text,''), COALESCE(subtitle,'')
            FROM articles
            WHERE is_leaf = 1
        """)
        conn.commit()
        cursor.execute("SELECT COUNT(*) as c FROM articles_fts")
        return cursor.fetchone()['c']
    finally:
        conn.close()
```

---

## Task 2: Tạo `scripts/search.py`

### File mới: `scripts/search.py`

**Interface CLI:**

```bash
# Tìm kiếm cơ bản
python scripts/search.py "king cobra venom"

# Giới hạn kết quả
python scripts/search.py "king cobra venom" --limit 5

# Lọc theo category
python scripts/search.py "migration routes" --category animal

# Output JSON (default) hoặc markdown
python scripts/search.py "coral reef bleaching" --format markdown

# Rebuild index (chạy 1 lần sau khi import hàng loạt)
python scripts/search.py --rebuild
```

**Output JSON (default):**

```json
{
  "query": "king cobra venom mechanism",
  "total_results": 5,
  "results": [
    {
      "rank": 1,
      "book": "How Snakes Work",
      "chapter": "Venom Systems",
      "section": "Neurotoxic Mechanisms",
      "word_count": 312,
      "snippet": "The king cobra delivers venom via <b>proteolytic enzymes</b>...",
      "passage": "King cobras possess one of the most complex venom systems..."
    }
  ]
}
```

**Output Markdown (--format markdown):**

```markdown
## Search: "king cobra venom mechanism" — 5 results

### [1] How Snakes Work › Venom Systems › Neurotoxic Mechanisms
*312 words | category: animal*

King cobras possess one of the most complex venom systems...

---

### [2] ...
```

### Implementation notes

- Script phải hoạt động standalone: `python scripts/search.py` từ project root
- Import `DatabaseManager` từ `src/extract_app/core/database`
- Dùng `sys.path.insert(0, str(Path(__file__).parent.parent))` để resolve import
- `--rebuild` flag: gọi `db.rebuild_fts_index()`, in số records, exit
- Nếu DB chưa có FTS table → tự động rebuild trước khi search
- Nếu không có kết quả → in thông báo rõ ràng, không crash

---

## Task 3: Test thực tế

Sau khi implement, chạy 3 query test để verify:

```bash
python scripts/search.py "rắn hổ mang" --limit 3
python scripts/search.py "elephant social behavior" --limit 3  
python scripts/search.py "cactus water storage" --category plant --limit 3
```

Kết quả mong đợi:
- Mỗi query trả về ít nhất 1 kết quả có passage dài > 50 từ
- `book_title` và `chapter_title` phải có giá trị (không null/empty)
- Ranking hợp lý: cuốn chuyên sâu về chủ đề đó phải xuất hiện trước

---

## Task 4: Cập nhật `ROADMAP.md`

Thêm vào ROADMAP section mới:

```markdown
## Phase 7: Context Retrieval (FTS5 Search)
- [x] Metadata audit: phát hiện category field confusion
- [x] `site_category` backfill vào content.md + books DB table
- [x] FTS5 virtual table + auto-sync triggers
- [x] `search_content()` method in DatabaseManager (filter by site_category)
- [x] `scripts/search.py` CLI interface
- [ ] Integration với Antigravity article pipeline
```

---

## Acceptance Criteria

**Task 0:**
- [ ] `scripts/backfill_site_category.py` chạy thành công, log "X files updated"
- [ ] `content.md` của Cheetah có `site_category: animal`
- [ ] `content.md` của Cacti and Succulents có `site_category: plant`
- [ ] `books.site_category` trong DB đã được backfill (verify: `SELECT site_category, COUNT(*) FROM books GROUP BY site_category`)

**Task 1-2:**
- [ ] `articles_fts` table tồn tại trong extract.db
- [ ] 3 triggers auto-sync hoạt động (INSERT/UPDATE/DELETE)
- [ ] `python scripts/search.py "king cobra" --limit 3` trả về JSON hợp lệ với `site_category: animal`
- [ ] `python scripts/search.py --rebuild` chạy không crash, in số records
- [ ] `--category animal` filter: kết quả chỉ từ books có `site_category=animal` (không có plant)
- [ ] `--category plant` filter: kết quả chỉ từ plant books
- [ ] `--format markdown` output đọc được
- [ ] Thêm vào ROADMAP.md

---

## Không cần làm (scope của spec này)

- KHÔNG build GUI search trong app
- KHÔNG tích hợp với WordPress pipeline ngay (bước tiếp theo)
- KHÔNG thêm ChromaDB / semantic search (Phase 2, sau khi FTS5 hoạt động tốt)
- KHÔNG thay đổi extraction pipeline

---

## Context cho Antigravity

DB path: lấy từ `config.get_user_data_dir() / "extract.db"`  
DB schema: xem `src/extract_app/core/database.py`

### ⚠️ Phân biệt các category fields — QUAN TRỌNG

| Field | Nơi lưu | Giá trị | Dùng cho |
|-------|---------|---------|---------|
| `books.category` | DB | Taxonomic class (`Reptilia`, `Felidae`...) | Taxonomy UI — **KHÔNG dùng cho search filter** |
| `books.site_category` | DB (field mới, thêm bởi spec này) | `animal`\|`plant`\|`overlap`\|`off` | **Search filter `--category`** |
| `content.md: category` | Filesystem | Taxonomic class | Metadata file — **KHÔNG dùng cho search filter** |
| `content.md: folder_category` | Filesystem | Taxonomic family (đôi khi sai) | **KHÔNG dùng** |
| `content.md: site_category` | Filesystem (backfill bởi Task 0) | `animal`\|`plant`\|`overlap`\|`off` | Metadata file — mirror của DB field |

**Rule:** Search filter luôn dùng `books.site_category` trong DB. Không bao giờ dùng `books.category`.
