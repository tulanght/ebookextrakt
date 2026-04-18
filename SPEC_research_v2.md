# SPEC: Research Pipeline v2 — Section-level Research + Outline Templates

**Mục đích:** Antigravity viết bài dựa trên outline có sẵn, nhận được context được
research tối ưu theo từng section — thay vì 1 file chung cho cả bài.

**Thực hiện bởi:** Antigravity
**Thay thế:** `SPEC_research_brief.md` v1 (chưa implement, bỏ qua)
**Phụ thuộc:** Thêm 1 method vào `database.py`, tạo 1 script mới, 3 template files

---

## Tổng quan thay đổi

| File | Hành động |
|------|-----------|
| `src/extract_app/core/database.py` | Thêm method `fts_search_raw()` + `fts_search_phrase()` |
| `scripts/research.py` | **GHI ĐÈ** (v1 chưa implement) — version mới section-level |
| `templates/outline/species-profile.md` | **TẠO MỚI** |
| `templates/outline/comparison.md` | **TẠO MỚI** |
| `templates/outline/listicle.md` | **TẠO MỚI** |
| `context/` | Auto-create khi chạy script |

---

## 1. Input format — Research Plan JSON

Antigravity tự tạo file này từ outline trước khi gọi `research.py`.

**Vị trí:** `context/{slug}/_plan.json`

```json
{
  "topic": "Hổ Chúa",
  "slug": "ho-chua",
  "article_type": "species-profile",
  "target_length": 1800,
  "default_category": "animal",
  "sections": [
    {
      "id": "03-morphology",
      "title": "Đặc điểm hình thái",
      "queries": [
        "\"king cobra\" size length adult",
        "NEAR(\"king cobra\" coloration, 15)",
        "\"Ophiophagus hannah\" physical description"
      ],
      "category": "animal",
      "target_passages": 5,
      "require_concrete": true
    },
    {
      "id": "05-hunting",
      "title": "Tập tính săn mồi",
      "queries": [
        "\"king cobra\" hunting prey",
        "NEAR(\"king cobra\" snake prey, 20)",
        "\"Ophiophagus\" feeding behavior ophiophagous"
      ],
      "category": "animal",
      "target_passages": 4
    },
    {
      "id": "07-venom",
      "title": "Nọc độc",
      "queries": [
        "NEAR(\"king cobra\" venom, 10)",
        "\"king cobra\" neurotoxin yield",
        "\"king cobra\" bite symptoms"
      ],
      "category": "animal",
      "target_passages": 4
    }
  ]
}
```

**Quy tắc FTS5 syntax trong `queries`:**
- Cụm từ đa từ PHẢI wrap trong dấu `"..."`: `"king cobra"` (không phải `king cobra`)
- Proximity: `NEAR("king cobra" venom, 15)` = cụm "king cobra" trong vòng 15 từ của "venom"
- Kết hợp: `"king cobra" AND (venom OR toxin)`

---

## 2. CLI Interface

```bash
# Chạy research theo plan
python scripts/research.py --plan context/ho-chua/_plan.json

# Overwrite kết quả cũ
python scripts/research.py --plan context/ho-chua/_plan.json --force

# Dry run: xem plan sẽ search gì, không chạy FTS5
python scripts/research.py --plan context/ho-chua/_plan.json --dry-run
```

**Output structure:**
```
context/ho-chua/
├── _plan.json              ← input (Antigravity tạo)
├── _summary.md             ← overview + gaps report (script tạo)
├── 03-morphology.md        ← 1 file per section
├── 05-hunting.md
├── 07-venom.md
└── ...
```

---

## 3. Method mới trong `database.py`

Thêm 2 methods sau `search_content()`:

### `fts_search_raw()` — low-level FTS5 query

```python
def fts_search_raw(
    self,
    fts_query: str,              # FTS5 syntax RAW (có thể chứa "", NEAR, AND/OR)
    site_category: str = None,
    limit: int = 100,
    min_words: int = 80,
    exclude_article_ids: list[int] = None  # anti-duplication
) -> list[dict]:
    """
    Raw FTS5 search with optional article exclusion.
    Returns: article_id, book_id, book_title, site_category,
             chapter_title, section_title, passage, rank, word_count
    """
    conn = self._get_connection()
    try:
        cursor = conn.cursor()
        params = [fts_query]

        where_extra = ""
        if site_category:
            where_extra += " AND b.site_category = ?"
            params.append(site_category)

        if exclude_article_ids:
            placeholders = ','.join('?' * len(exclude_article_ids))
            where_extra += f" AND a.id NOT IN ({placeholders})"
            params.extend(exclude_article_ids)

        params.append(limit)

        cursor.execute(f"""
            SELECT
                a.id AS article_id,
                b.id AS book_id,
                b.title AS book_title,
                b.site_category AS site_category,
                c.title AS chapter_title,
                a.subtitle AS section_title,
                a.content_text AS passage,
                articles_fts.rank AS rank,
                a.word_count
            FROM articles_fts
            JOIN articles a ON a.id = articles_fts.rowid
            JOIN chapters c ON c.id = a.chapter_id
            JOIN books b ON b.id = c.book_id
            WHERE articles_fts MATCH ?
              AND a.is_leaf = 1
              AND a.word_count >= {min_words}
              {where_extra}
            ORDER BY rank
            LIMIT ?
        """, params)

        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
```

**Lưu ý:** Giữ `search_content()` nguyên — UI đang dùng. KHÔNG refactor.

---

## 4. `scripts/research.py` — Logic chính

### Pipeline

```
1. Load _plan.json
2. Init global_used_ids = set()  (anti-duplication across sections)
3. For each section in plan.sections:
   a. Run từng query trong section.queries → pool results (dedup by article_id)
   b. Rank lại pool: score = fts_rank + concreteness_bonus - book_overlap_penalty
   c. Pick top N passages (section.target_passages), max 1 passage/book trong section
   d. Truncate passages at sentence boundary (~150 words)
   e. Add article_ids into global_used_ids
   f. Write {section.id}.md
4. Generate _summary.md with gap report
```

### Scoring function

```python
def _score_passage(passage: dict, section: dict, used_book_ids_in_section: set) -> float:
    """
    Lower = better (giống FTS5 rank convention).
    """
    base = passage['rank']  # already negative, more negative = more relevant

    # Bonus concreteness (nếu section.require_concrete = True)
    if section.get('require_concrete'):
        concrete = _count_concrete_markers(passage['passage'])
        base -= concrete * 0.3  # càng nhiều fact cụ thể càng tốt

    # Penalty nếu cuốn đã được dùng trong section này
    if passage['book_id'] in used_book_ids_in_section:
        base += 5.0  # đẩy rank xuống mạnh

    return base


def _count_concrete_markers(text: str) -> int:
    """Đếm số liệu, tên khoa học, đơn vị đo — markers của fact cụ thể."""
    import re
    count = 0
    count += len(re.findall(r'\b\d+(?:\.\d+)?\b', text))           # numbers
    count += len(re.findall(r'\b[A-Z][a-z]+ [a-z]+\b', text))      # scientific names
    count += len(re.findall(r'\b\d+\s*(?:kg|g|m|cm|ft|in|lb|oz|mph|kph|km|mi)\b', text, re.I))  # units
    count += len(re.findall(r'\b(?:19|20)\d{2}\b', text))          # years
    return count
```

### Passage truncation

```python
def _truncate_at_sentence(text: str, max_words: int = 150) -> str:
    # Strip markdown headers first
    text = re.sub(r'^#+\s+.+$', '', text, flags=re.MULTILINE).strip()
    text = re.sub(r'\n{2,}', '\n\n', text)

    words = text.split()
    if len(words) <= max_words:
        return text

    # Tìm boundary '. ' trong window [max_words-20, max_words+30]
    window_start_idx = len(' '.join(words[:max_words - 20]))
    window_end_idx = len(' '.join(words[:max_words + 30]))
    snippet = text[:window_end_idx]

    cut = snippet.rfind('. ', window_start_idx)
    if cut == -1:
        return ' '.join(words[:max_words]) + '...'
    return snippet[:cut + 1]
```

### Section output format

**File `context/{slug}/{section_id}.md`:**

```markdown
# Section: Đặc điểm hình thái
Section ID: 03-morphology | Passages: 4 sources | ~580 words

## Queries used
- `"king cobra" size length adult`
- `NEAR("king cobra" coloration, 15)`
- `"Ophiophagus hannah" physical description`

---

### [1] Snakes of the World · animal
> Chapter 11 › King cobra morphology | 320 words in source | rank -18.4

King cobra averages 3.5-4 m (11.5-13 ft), with record 5.5 m (18 ft).
Adults uniformly olive, tan, or brown dorsally. Juveniles marked with
bold yellow chevrons on black background. Scales smooth and glossy.
Distinguished from true cobras (Naja) by larger body, occipital shields
on head, and narrower hood when threatened...

---

### [2] Venomous Snakes of the World · animal
> Chapter 13 › King Cobra | 409 words in source | rank -15.2

Ophiophagus hannah. Description and Identification: This is the world's
longest venomous snake, with a record length of over 18 feet. Most are
fully grown at about 12 feet. Adults are usually uniformly colored
dorsally, and the ground color is light yellow brown, tan, or olive
brown...

---

### [3] Nature Guide Snakes · animal
> Snakes 22 › King cobra | 216 words in source | rank -13.8

...
```

### `_summary.md` — Gap analysis

```markdown
# Research Summary: Hổ Chúa
Slug: ho-chua | Article type: species-profile | Date: 2026-04-18

## Sections
| ID | Title | Target | Found | Books | Status |
|----|-------|--------|-------|-------|--------|
| 03-morphology | Đặc điểm hình thái | 5 | 5 | 5 | ✅ OK |
| 05-hunting | Tập tính săn mồi | 4 | 3 | 3 | ⚠ Short |
| 07-venom | Nọc độc | 4 | 4 | 4 | ✅ OK |
| 09-conservation | Bảo tồn | 3 | 1 | 1 | ❌ Gap |

## Gaps — cần bổ sung từ web search
- **09-conservation**: chỉ tìm được 1 passage trong 91k articles.
  Gợi ý: web search "king cobra IUCN status", "king cobra Vietnam protection law"

## Vietnamese context (không có trong ebooks English)
Các section sau cần web search tiếng Việt:
- Phân bố tại Việt Nam
- Tên gọi địa phương (Hổ Mang Chúa vs Hổ Chúa)
- Văn hóa Việt liên quan

## Total stats
- Sources: 13 unique books
- Total passages: 13
- Total research words: ~1,890
- Estimated token usage: ~2,500
```

---

## 5. Outline Templates — `templates/outline/`

Tạo 3 markdown templates để Antigravity dùng làm base khi lên outline bài.

### `templates/outline/species-profile.md`

```markdown
# Species Profile Template

**Dùng cho:** Bài giới thiệu 1 loài động vật/thực vật cụ thể.
**Target length:** 1,500-2,500 từ
**Primary keyword pattern:** `[tên loài]` + geographic/descriptor

## Suggested structure

1. **Intro & Hook** (100-150 từ)
   - Điều gì khiến loài này đặc biệt
   - Tên khoa học + tên tiếng Việt/địa phương
   - Teaser vào các section chính

2. **Danh pháp & Phân loại khoa học** (100-200 từ)
   - Binomial nomenclature
   - Họ/Bộ
   - Ai mô tả đầu tiên, năm nào

3. **Đặc điểm hình thái** (200-300 từ)
   - Kích thước, cân nặng
   - Màu sắc, đặc điểm phân biệt
   - Khác biệt giữa đực/cái, non/trưởng thành

4. **Phân bố & Môi trường sống** (200-250 từ)
   - Vùng địa lý (thế giới + VN nếu có)
   - Loại habitat
   - Độ cao, khí hậu

5. **Tập tính & Hành vi xã hội** (200-300 từ)
   - Đơn độc hay bầy đàn
   - Hoạt động ngày/đêm
   - Giao tiếp, lãnh thổ

6. **Chế độ ăn & Săn mồi** (200-250 từ)
   - Ăn gì
   - Cách săn/kiếm ăn
   - Vai trò trong chuỗi thức ăn

7. **Sinh sản & Vòng đời** (200-250 từ)
   - Mùa sinh sản
   - Số con, thời gian thai/trứng
   - Tuổi thọ

8. **Mối đe dọa & Bảo tồn** (150-200 từ)
   - Tình trạng IUCN
   - Threats chính
   - Chương trình bảo tồn

9. **Văn hóa & Con người** (100-200 từ, optional)
   - Ý nghĩa văn hóa
   - Ở Việt Nam (nếu có)

10. **Kết luận & FAQ** (100-150 từ)

## Query patterns cho research

Tham khảo `context/ho-chua/_plan.json` làm mẫu.

Mỗi section cần 3-4 queries với phrase match + proximity.
```

### `templates/outline/comparison.md`

```markdown
# Comparison Template (A vs B)

**Dùng cho:** So sánh 2 loài thường bị nhầm lẫn.
**Ví dụ:** Alpaca vs Llama, Cá Sấu vs Cá Sấu Mõm Dài
**Target length:** 1,200-1,800 từ

## Suggested structure

1. **Intro — Vì sao hay bị nhầm** (150 từ)
2. **Bảng so sánh nhanh** (table — 100 từ + table)
3. **Khác biệt phân loại học** (200 từ)
4. **Khác biệt hình thái** (300 từ)
5. **Khác biệt hành vi** (250 từ)
6. **Khác biệt phân bố/môi trường sống** (200 từ)
7. **Which is which? Cách phân biệt nhanh** (200 từ)
8. **Kết luận** (100 từ)

## Query patterns

Mỗi section chạy query cho CẢ 2 loài, ví dụ:

```json
"queries": [
  "\"alpaca\" size weight adult",
  "\"llama\" size weight adult"
]
```

Sau đó viết section bằng cách đối chiếu 2 tập passages.
```

### `templates/outline/listicle.md`

```markdown
# Listicle Template (Top N)

**Dùng cho:** Top 10 X, 5 loài nguy hiểm nhất, v.v.
**Target length:** 2,000-3,000 từ (200-300 từ/item)

## Suggested structure

1. **Intro & Criteria** (200 từ)
   - Tiêu chí chọn items
   - Disclaimer (nếu có)

2. **Items (N entries)** — mỗi entry 250 từ
   - Name (tên khoa học + tiếng Việt)
   - Hook (1 fact ấn tượng)
   - Key characteristics (2-3 bullets)
   - Fun fact / Danger factor

3. **Honorable mentions** (150 từ, optional)
4. **Kết luận** (100 từ)

## Query patterns

Mỗi item là 1 "mini section" với queries riêng:

```json
"sections": [
  {
    "id": "item-01-king-cobra",
    "title": "Hổ Chúa",
    "queries": ["\"king cobra\" venom length", "\"Ophiophagus hannah\""],
    "target_passages": 3
  },
  {
    "id": "item-02-inland-taipan",
    "title": "Rắn Taipan Nội Địa",
    "queries": ["\"inland taipan\" venom toxicity", "\"Oxyuranus microlepidotus\""],
    "target_passages": 3
  }
]
```
```

---

## 6. Workflow đầy đủ cho Antigravity

Khi bắt đầu session viết bài "Hổ Chúa":

```bash
# Bước 1: Đọc template phù hợp
cat templates/outline/species-profile.md

# Bước 2: Dịch topic sang English, tạo research plan
# Antigravity tự viết _plan.json dựa trên template
mkdir -p context/ho-chua
# → context/ho-chua/_plan.json

# Bước 3: Chạy research
python scripts/research.py --plan context/ho-chua/_plan.json

# Bước 4: Đọc _summary.md để biết gap ở đâu
cat context/ho-chua/_summary.md

# Bước 5: Web search cho gaps (nếu có)
# Antigravity tự quyết định gap nào cần bổ sung

# Bước 6: Viết bài section-by-section
# Đọc 03-morphology.md → viết section "Đặc điểm hình thái"
# Đọc 05-hunting.md → viết section "Tập tính săn mồi"
# ...
```

---

## 7. Acceptance Criteria

- [ ] `python scripts/research.py --plan {file.json}` chạy không crash
- [ ] Output folder có đủ: `_plan.json`, `_summary.md`, 1 file/section
- [ ] Mỗi section file có ≥ 3 passages từ ≥ 3 cuốn sách **khác nhau**
- [ ] 1 passage chỉ xuất hiện trong tối đa 1 section (anti-duplication toàn plan)
- [ ] Passage truncate tại sentence boundary, không cắt giữa câu, ~150 words
- [ ] `_summary.md` liệt kê rõ sections đủ/thiếu/gap
- [ ] Phrase queries (`"king cobra"`) hoạt động đúng FTS5 syntax
- [ ] Proximity queries (`NEAR("king cobra" venom, 15)`) hoạt động đúng
- [ ] `--dry-run` chỉ in plan, không chạy query, không tạo file
- [ ] `--force` overwrite folder cũ
- [ ] 3 template files được tạo đúng vị trí `templates/outline/`
- [ ] Concreteness scoring: passage có số liệu/tên khoa học được ưu tiên

---

## 8. Không cần làm

- Không cần tự generate outline từ brief — Antigravity làm manual bằng template
- Không cần tự extract keywords từ outline — Antigravity tự viết queries vào `_plan.json`
- Không cần integrate với keyword search volume tool — task riêng
- Không cần UI mới — CLI only
- Không cần sửa `search_content()` hay `SearchView` hiện có
- Không cần cache research results — SQLite FTS5 đã đủ nhanh
