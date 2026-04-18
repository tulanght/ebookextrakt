# SPEC: Research Brief Generator — `scripts/research.py`

**Mục đích:** Cho phép Antigravity (và Claude) tự động extract factual context
từ 91k+ articles đã index, phục vụ viết bài — không cần web search.

**Thực hiện bởi:** Antigravity
**Gọi bởi:** Antigravity tự gọi đầu mỗi session viết bài, từ workspace `kenhdongvat-seo`
**Output:** `ExtractPDF-EPUB/context/{slug}.md` — đọc trực tiếp làm context viết bài

**Phụ thuộc:**
- `search_content()` tại `database.py:904` — đã có, không sửa
- Thêm `search_research()` method mới vào `database.py` (xem mục 2)

---

## 1. CLI Interface

```bash
# Single query — phổ biến nhất
python scripts/research.py "king cobra"

# Multi-query — khi 1 topic cần nhiều góc (merge kết quả, 1 file output)
python scripts/research.py "king cobra" "cobra venom neurotoxin" "Ophiophagus habitat"

# Filter category
python scripts/research.py "cactus drought" --category plant

# Overwrite nếu file đã tồn tại
python scripts/research.py "king cobra" --force

# Batch từ file danh sách (mỗi dòng = 1 query, 1 file output)
python scripts/research.py --batch topics.txt

# Giới hạn số sách trả về (default 10)
python scripts/research.py "king cobra" --limit 12
```

**Lưu ý:** Query PHẢI là tiếng Anh. Antigravity có trách nhiệm dịch topic
tiếng Việt → English trước khi gọi script.
```
Topic: "Hổ Chúa" → query: "king cobra"
Topic: "Cá Voi Xanh" → query: "blue whale"
```

---

## 2. Method mới: `database.py` — `search_research()`

Thêm method sau `search_content()` (khoảng line 960):

```python
def search_research(
    self,
    queries: list[str],          # 1 hoặc nhiều queries, merge kết quả
    site_category: str = None,   # filter: 'animal' | 'plant' | 'overlap' | None
    top_books: int = 10,         # số sách trả về
    min_words: int = 80,         # bỏ qua passages quá ngắn
    passage_words: int = 150     # cắt passage tại n words
) -> list[dict]:
    """
    Research-optimized search: trả về 1 passage tốt nhất từ mỗi cuốn sách,
    đa dạng nguồn, đã cắt theo word budget.

    Returns list of dicts:
        book_title, site_category, chapter_title, section_title,
        passage (truncated), source_words (original word count), rank
    """
```

### Logic chi tiết:

```python
# Step 1: Chạy FTS5 cho từng query, pool tất cả results
all_results = []
for query in queries:
    rows = self._fts_search_raw(query, site_category, limit=200, min_words=min_words)
    all_results.extend(rows)

# Step 2: Dedup — giữ passage có rank tốt nhất (thấp nhất) cho mỗi book
best_per_book = {}
for row in all_results:
    book_id = row['book_id']
    if book_id not in best_per_book or row['rank'] < best_per_book[book_id]['rank']:
        best_per_book[book_id] = row

# Step 3: Sort by rank, lấy top N books
top = sorted(best_per_book.values(), key=lambda r: r['rank'])[:top_books]

# Step 4: Truncate passage tại sentence boundary
for item in top:
    item['passage'] = _truncate_at_sentence(item['passage'], passage_words)

return top
```

### Helper `_truncate_at_sentence()`:

```python
def _truncate_at_sentence(text: str, max_words: int) -> str:
    """Cắt text tại boundary câu gần nhất với max_words."""
    words = text.split()
    if len(words) <= max_words:
        return text
    # Tìm dấu câu cuối trong window max_words → max_words+30
    window = ' '.join(words[:max_words + 30])
    # Tìm vị trí '. ' cuối cùng trong window
    cut = window.rfind('. ', 0, len(' '.join(words[:max_words])) + 150)
    if cut == -1:
        return ' '.join(words[:max_words]) + '...'
    return window[:cut + 1] + '..'
```

### Helper `_fts_search_raw()` (internal):

Tách phần SQL của `search_content()` thành method riêng để `search_research()` dùng lại.
Signature: `_fts_search_raw(query, site_category, limit, min_words) -> list[dict]`

---

## 3. `scripts/research.py` — Script chính

### Slug generation:

```python
import re

def to_slug(query: str) -> str:
    """'King Cobra' → 'king-cobra'"""
    slug = query.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug[:60]  # max 60 chars
```

Slug lấy từ **query đầu tiên** trong list.

### Idempotency:

```python
output_path = CONTEXT_DIR / f"{slug}.md"
if output_path.exists() and not args.force:
    print(f"[SKIP] {output_path.name} đã tồn tại. Dùng --force để ghi đè.")
    sys.exit(0)
```

### Output format (`context/{slug}.md`):

```markdown
# Research Brief: King Cobra
Queries: "king cobra", "cobra venom neurotoxin" | Date: 2026-04-18
Sources: 8 books | Category: all | ~1,243 words total

---

### [1] Venomous Snakes of the World · animal
> Chapter 13 › King Cobra | 409 words in source

World's longest venomous snake, record length over 18 feet. Venom:
post-synaptic neurotoxins — less potent per unit than smaller cobras
but huge quantity. Large specimen's venom glands can yield enough to
kill 36 humans. Found from India/Nepal east to China, south through
SE Asia to Philippines, Java, Celebes. Feeds mostly on other snakes.
Known among zookeepers for intelligence and fearlessness when cornered..

---

### [2] Animal The Definitive Visual Guide · animal
> Elapids › King cobra | 246 words in source

Raises front third of body to 5ft when threatened, spreads narrow hood.
May strike downward. Sometimes monogamous — pairs remain together during
breeding season. Lays 21-40 eggs in piles of dead vegetation, both parents
guard until hatching. May live 20+ years in captivity..

---

### [3] Nature Guide Snakes and Other Reptiles · animal
> Snakes 22 › King cobra | 216 words in source

...
```

### Console output khi chạy:

```
Searching: "king cobra" (+ 1 related queries)...
Found 8 relevant books from 91,521 articles.
Output: C:/Users/AORUS/Documents/Projects/ExtractPDF-EPUB/context/king-cobra.md
Words: ~1,243 | Ready for Antigravity.
```

### Khi không tìm thấy kết quả:

```
[WARNING] Không tìm thấy kết quả cho "saola vietnam" trong DB.
Gợi ý: Thử query tiếng Anh khác, hoặc dùng web search cho topic này.
```
Không tạo file, exit 0.

---

## 4. Batch mode (`--batch topics.txt`)

Format `topics.txt`:
```
king cobra
blue whale
komodo dragon
saltwater crocodile
```

Mỗi dòng = 1 query riêng → 1 file output riêng.
Dòng trống và dòng bắt đầu bằng `#` → bỏ qua.

Output:
```
[1/4] king cobra → context/king-cobra.md ✓
[2/4] blue whale → context/blue-whale.md ✓
[3/4] komodo dragon → context/komodo-dragon.md ✓
[4/4] saltwater crocodile → context/saltwater-crocodile.md ✓
Done. 4 briefs generated.
```

---

## 5. Cách Antigravity gọi từ kenhdongvat-seo

Đầu mỗi session viết bài:

```bash
# Bước 1: Generate research brief
cd "C:/Users/AORUS/Documents/Projects/ExtractPDF-EPUB"
python scripts/research.py "king cobra" "cobra venom" "Ophiophagus"

# Bước 2: Đọc context file
# Path: C:/Users/AORUS/Documents/Projects/ExtractPDF-EPUB/context/king-cobra.md

# Bước 3: Nếu context đủ (≥ 3 sources) → viết bài
# Nếu context < 3 sources → bổ sung web search rồi viết
```

---

## 6. Cấu trúc project sau khi implement

```
ExtractPDF-EPUB/
├── scripts/
│   ├── research.py          ← FILE MỚI
│   ├── search.py            ← giữ nguyên (CLI cho user)
│   └── bulk_import_extracted.py
├── context/                 ← THƯ MỤC MỚI (auto-create)
│   ├── king-cobra.md
│   ├── blue-whale.md
│   └── ...
└── src/extract_app/core/
    └── database.py          ← thêm search_research() + _fts_search_raw()
```

---

## Acceptance Criteria

- [ ] `python scripts/research.py "king cobra"` → tạo `context/king-cobra.md`
- [ ] File chứa ≥ 5 sections từ ≥ 5 cuốn sách KHÁC NHAU (diversity)
- [ ] Mỗi passage ≤ 200 words, cắt tại sentence boundary (không cắt giữa câu)
- [ ] Header file có: queries, date, số sách, tổng word count
- [ ] Multi-query merge: `research.py "cobra" "Ophiophagus"` → 1 file, không duplicate sách
- [ ] Idempotent: chạy lại lần 2 → `[SKIP]`, không overwrite
- [ ] `--force` → overwrite
- [ ] `--batch topics.txt` → 4 topics → 4 files
- [ ] Khi 0 kết quả → warning rõ, không crash, không tạo file rỗng
- [ ] Script chạy được từ bất kỳ working directory nào (dùng absolute path đến DB)

---

## Không cần làm

- Không cần UI — script CLI only
- Không cần dịch tiếng Việt → English (Antigravity tự lo)
- Không cần lưu search history vào DB
- Không cần thêm table mới vào DB
- Không sửa `search.py` (script cũ cho user) hay `search_content()` (đang dùng bởi UI)
