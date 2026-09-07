# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: scripts/bulk_import_extracted.py
# Version: 1.2.0
# Author: Antigravity
# Description: Bulk imports ebooks from filesystem into SQLite database with FTS mapping,
#              supporting both content.md and content.txt, prefix/exact deduplication,
#              and idempotent updates.
# --------------------------------------------------------------------------------

import argparse
import sys
import os
import json
import re
import yaml
import time
from typing import Optional, Tuple, List, Dict
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding='utf-8')

# Add project root to path so we can import src
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.extract_app.core.database import DatabaseManager
from src.extract_app.shared.constants import MIN_ARTICLE_BYTES


class AmbiguousBookError(Exception):
    """Raised when prefix matching finds more than 1 distinct candidate book in DB."""
    def __init__(self, folder_name: str, candidate_count: int):
        self.folder_name = folder_name
        self.candidate_count = candidate_count
        super().__init__(f"Ambiguous matches ({candidate_count}) for folder '{folder_name}'")


def _log_ambiguous_prefix_match(folder_name: str, prefix_key: str, candidate_groups: dict):
    """Logs ambiguous prefix match to docs/handoff/ANTIGRAVITY-ASK.md."""
    ask_file = project_root / "docs" / "handoff" / "ANTIGRAVITY-ASK.md"
    now_str = time.strftime("%Y-%m-%d %H:%M")
    
    cand_lines = []
    for k, rows in candidate_groups.items():
        for r in rows:
            cand_lines.append(f"- ID {r.get('id')}: '{r.get('title')}' (source: {r.get('source_path')})")
    cands_str = "\n".join(cand_lines)
    
    entry = f"""
## [{now_str}] Trùng lặp Prefix nhiều hơn 1 ứng viên cho '{folder_name}'
**Bối cảnh:** bulk_import_extracted.py quét thư mục '{folder_name}' (prefix: '{prefix_key}').
**Vấn đề:** Phát hiện {len(candidate_groups)} ứng viên title khác nhau trong DB:
{cands_str}
**Phương án đề xuất:**
- A: Bỏ qua không nhập thư mục này (đang áp dụng tự động).
- B: Chỉ định thủ công Book ID cần gộp.
**Cần Claude chốt:** Xác nhận gộp vào Book ID nào hoặc giữ nguyên bỏ qua.
"""
    try:
        with open(ask_file, "a", encoding="utf-8") as f:
            f.write("\n" + entry.strip() + "\n")
        print(f"[WARN] Ambiguous prefix match for '{folder_name}' -> logged to {ask_file.name}")
    except Exception as e:
        print(f"[ERROR] Failed to write to {ask_file}: {e}")


def parse_content_md(filepath: Path) -> tuple[dict, str]:
    """Returns (frontmatter_dict, body_text). Handles both .md (with frontmatter) and .txt (plain text)."""
    try:
        text = filepath.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return {}, ""
        
    parts = text.split('---', 2)
    if len(parts) < 3:
        body = text.strip()
        body = re.sub(r'\n+> \*\*Nguồn:\*\*.*$', '', body, flags=re.MULTILINE).strip()
        body = re.sub(r'\[Image Anchor:[^\]]*\]', '', body)
        return {}, body
    
    fm_text = parts[1]
    body = parts[2].strip()
    
    try:
        fm = yaml.safe_load(fm_text) or {}
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError:
        fm = {}
        
    # Lọc noise trong body (remove custom footer and image anchors)
    body = re.sub(r'\n+> \*\*Nguồn:\*\*.*$', '', body, flags=re.MULTILINE).strip()
    body = re.sub(r'\[Image Anchor:[^\]]*\]', '', body)
    return fm, body


def get_chapter_folder(content_file_path: Path, book_root: Path) -> Path:
    """Trả về second-level subfolder (chapter) chứa file này."""
    relative = content_file_path.relative_to(book_root)
    if len(relative.parts) <= 1:
        return book_root
    return book_root / relative.parts[0]


def get_book_content_files(book_folder: Path) -> list[Path]:
    """
    Returns list of content files in book_folder.
    Prioritizes content.md if present; falls back to content.txt.
    Filters out files smaller than MIN_ARTICLE_BYTES (400 bytes).
    """
    md_files = [f for f in book_folder.rglob("content.md") if f.is_file()]
    if md_files:
        files = md_files
    else:
        files = [f for f in book_folder.rglob("content.txt") if f.is_file()]
        
    valid_files = []
    for f in sorted(files):
        try:
            if f.stat().st_size >= MIN_ARTICLE_BYTES:
                valid_files.append(f)
        except OSError:
            pass
    return valid_files


def normalize_title(t: str) -> str:
    """
    Normalizes a book title for deduplication comparison:
    lowercase, strips leading index numbers like '01 - ', and removes whitespace, hyphens, quotes, punctuation.
    """
    if not t:
        return ""
    t = re.sub(r'^\d+\s*-\s*', '', t)
    return re.sub(r"[\s\-_'\"`\u2018\u2019\u201c\u201d.,:;!?()]", "", t).lower()


def find_existing_book(db: DatabaseManager, title: str, book_folder: Optional[Path] = None) -> Optional[dict]:
    """
    Finds an existing book record in DB by:
    - Step 1: Exact match on normalized title (matching DB title or source_path stem).
    - Step 2: If no exact match, prefix match on DB title starting with normalized folder name
              (condition: normalized folder name length >= 8 characters).
              - If exactly 1 distinct candidate -> return candidate dict.
              - If >1 distinct candidates -> log to docs/handoff/ANTIGRAVITY-ASK.md, raise AmbiguousBookError to skip.
    """
    target_norm = normalize_title(title) if title else ""
    folder_norm = normalize_title(book_folder.name) if book_folder else ""
    
    conn = db._get_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, source_path, site_category, author, published_year FROM books")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    
    # Bước 1: So khớp title đã chuẩn hóa CHÍNH XÁC (như hiện tại)
    for row in rows:
        db_title_norm = normalize_title(row["title"])
        if target_norm and db_title_norm == target_norm:
            return row
        if folder_norm and db_title_norm == folder_norm:
            return row
        if row.get("source_path"):
            db_source_stem_norm = normalize_title(Path(row["source_path"]).stem)
            if target_norm and db_source_stem_norm == target_norm:
                return row
            if folder_norm and db_source_stem_norm == folder_norm:
                return row

    # Bước 2: Khớp prefix nếu tên thư mục đã chuẩn hóa dài >= 8 ký tự
    prefix_key = folder_norm if folder_norm else target_norm
    if len(prefix_key) >= 8:
        candidate_groups: Dict[str, List[dict]] = {}
        for row in rows:
            db_title_norm = normalize_title(row["title"])
            db_source_stem_norm = normalize_title(Path(row["source_path"]).stem) if row.get("source_path") else ""
            
            matched_key = None
            if db_title_norm and db_title_norm.startswith(prefix_key):
                matched_key = db_title_norm
            elif db_source_stem_norm and db_source_stem_norm.startswith(prefix_key):
                matched_key = db_source_stem_norm
                
            if matched_key:
                candidate_groups.setdefault(matched_key, []).append(row)
                
        num_distinct_candidates = len(candidate_groups)
        if num_distinct_candidates == 1:
            # Có ĐÚNG 1 ứng viên -> coi là cùng sách
            first_key = next(iter(candidate_groups))
            return candidate_groups[first_key][0]
        elif num_distinct_candidates > 1:
            # Có NHIỀU HƠN 1 ứng viên -> KHÔNG tự gộp, ghi vào ANTIGRAVITY-ASK.md và bỏ qua
            _log_ambiguous_prefix_match(
                folder_name=book_folder.name if book_folder else title,
                prefix_key=prefix_key,
                candidate_groups=candidate_groups
            )
            raise AmbiguousBookError(
                folder_name=book_folder.name if book_folder else title,
                candidate_count=num_distinct_candidates
            )
            
    return None


def book_already_imported(db: DatabaseManager, book_folder: Path, title: str = None) -> bool:
    """Check if book already exists in DB by normalized title."""
    try:
        existing = find_existing_book(db, title or (book_folder.name if book_folder else ""), book_folder)
        return existing is not None
    except AmbiguousBookError:
        return True

def _save_node_batch_idempotent(db: DatabaseManager, cursor, chapter_id: int, node: dict, order_index: int, existing_articles: set):
    """Recursively saves a node and its children idempotently, skipping existing articles in the chapter."""
    subtitle = node.get('title', 'Untitled')
    children = node.get('children', [])
    is_leaf = len(children) == 0
    
    art_key = (chapter_id, subtitle.lower().strip())
    if art_key in existing_articles:
        article_id = None
    else:
        full_text = []
        images_to_save = []
        for content_type, data in node.get('content', []):
            if content_type == 'text':
                if isinstance(data, dict):
                    full_text.append(data.get('content', ''))
                else:
                    full_text.append(str(data))
            elif content_type == 'image' and isinstance(data, dict):
                anchor = data.get('anchor', '')
                if anchor:
                    full_text.append(f"[Image: {Path(anchor).name}]")
                    images_to_save.append({
                        'path': anchor,
                        'caption': data.get('caption', '')
                    })
        text_content = "\n\n".join(full_text)
        word_count = len(text_content.split()) if text_content else 0
        cursor.execute("""
            INSERT INTO articles (chapter_id, subtitle, content_text, order_index, is_leaf, word_count, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (chapter_id, subtitle, text_content, order_index, 1 if is_leaf else 0, word_count))
        article_id = cursor.lastrowid
        existing_articles.add(art_key)
        for img in images_to_save:
            cursor.execute("""
                INSERT INTO images (article_id, path, caption)
                VALUES (?, ?, ?)
            """, (article_id, img['path'], img['caption']))
            
    for i, child_node in enumerate(children):
        _save_node_batch_idempotent(db, cursor, chapter_id, child_node, order_index + 1000 + i, existing_articles)

def save_or_update_book(
    db: DatabaseManager,
    title: str,
    author: str,
    source_path: str,
    published_year: str,
    site_category: str,
    structured_content: list,
    existing_book_id: Optional[int] = None
) -> int:
    """
    Saves a new book or updates an existing book in-place idempotently in a single transaction.
    Returns book_id (or -1 on error).
    """
    conn = db._get_connection()
    try:
        cursor = conn.cursor()
        if existing_book_id:
            book_id = existing_book_id
            # 1. Update book metadata in-place
            if site_category:
                cursor.execute("UPDATE books SET site_category = ? WHERE id = ?", (site_category, book_id))
            if author:
                cursor.execute("UPDATE books SET author = ? WHERE id = ? AND (author IS NULL OR author = '')", (author, book_id))
            if published_year:
                cursor.execute("UPDATE books SET published_year = ? WHERE id = ? AND (published_year IS NULL OR published_year = '')", (published_year, book_id))
                
            # Fetch existing chapters for this book
            cursor.execute("SELECT id, title, order_index FROM chapters WHERE book_id = ?", (book_id,))
            existing_chapters = {row["title"].lower().strip(): row["id"] for row in cursor.fetchall()}
            
            # Fetch existing articles for all chapters in this book
            cursor.execute("""
                SELECT a.id, a.chapter_id, a.subtitle, a.order_index 
                FROM articles a 
                JOIN chapters c ON c.id = a.chapter_id 
                WHERE c.book_id = ?
            """, (book_id,))
            existing_articles = {(row["chapter_id"], (row["subtitle"] or "").lower().strip()) for row in cursor.fetchall()}
            
            for chap_idx, root_node in enumerate(structured_content):
                chap_title = root_node.get('title', f"Chapter {chap_idx+1}")
                chap_key = chap_title.lower().strip()
                if chap_key in existing_chapters:
                    chapter_id = existing_chapters[chap_key]
                else:
                    cursor.execute("""
                        INSERT INTO chapters (book_id, title, order_index)
                        VALUES (?, ?, ?)
                    """, (book_id, chap_title, chap_idx))
                    chapter_id = cursor.lastrowid
                    existing_chapters[chap_key] = chapter_id
                    
                _save_node_batch_idempotent(db, cursor, chapter_id, root_node, 0, existing_articles)
                
            conn.commit()
            return book_id
        else:
            cursor.execute("""
                INSERT INTO books (title, author, source_path, cover_path, published_year, site_category)
                VALUES (?, ?, ?, '', ?, ?)
            """, (title, author, source_path, published_year, site_category))
            book_id = cursor.lastrowid
            
            existing_articles = set()
            for chap_idx, root_node in enumerate(structured_content):
                chap_title = root_node.get('title', f"Chapter {chap_idx+1}")
                cursor.execute("""
                    INSERT INTO chapters (book_id, title, order_index)
                    VALUES (?, ?, ?)
                """, (book_id, chap_title, chap_idx))
                chapter_id = cursor.lastrowid
                _save_node_batch_idempotent(db, cursor, chapter_id, root_node, 0, existing_articles)
                
            conn.commit()
            return book_id
    except Exception as e:
        conn.rollback()
        print(f"[DB] Save/update error: {e}")
        return -1
    finally:
        conn.close()

def process_book(book_folder: Path, classification_cat: str, db: DatabaseManager, dry_run: bool = False) -> tuple[int, int]:
    """Process a single book folder. Returns (articles_count: int, status: int). status: 0=skip, 1=success, -1=error."""
    content_files = get_book_content_files(book_folder)
    if not content_files:
        return 0, 0
        
    book_frontmatter = {}
    for cf in content_files:
        fm, _ = parse_content_md(cf)
        if fm:
            book_frontmatter = fm
            break
            
    title = book_frontmatter.get("book_title") or book_folder.name
    author = book_frontmatter.get("author") or ""
    published_year = str(book_frontmatter.get("published_year") or "")
    source_path = str(book_folder)
    site_category = book_frontmatter.get("site_category") or classification_cat

    if dry_run:
        return len(content_files), 1

    chapters_map = {}
    for cf in content_files:
        chap_dir = get_chapter_folder(cf, book_folder)
        if chap_dir not in chapters_map:
            chapters_map[chap_dir] = []
        chapters_map[chap_dir].append(cf)
        
    structured_content = []
    sorted_chapter_dirs = sorted(chapters_map.keys(), key=lambda p: p.name)
    
    for chap_dir in sorted_chapter_dirs:
        chap_files = chapters_map[chap_dir]
        chap_root_rel = chap_dir.relative_to(book_folder)
        
        folder_nodes = {}
        for cf in chap_files:
            rel = cf.parent.relative_to(book_folder)
            fm, body = parse_content_md(cf)
            sec_idx = fm.get("section_index")
            if sec_idx is None:
                m = re.match(r'^(\d+)', rel.name)
                sec_idx = int(m.group(1)) if m else 0
            
            node = {
                "title": fm.get("article_title") or fm.get("chapter_title") or rel.name,
                "content": [("text", body)] if body else [],
                "children": [],
                "folder_path": rel,
                "order_index": sec_idx
            }
            folder_nodes[rel] = node
            
        if chap_root_rel not in folder_nodes:
            folder_nodes[chap_root_rel] = {
                "title": chap_dir.name,
                "content": [],
                "children": [],
                "folder_path": chap_root_rel,
                "order_index": int(chap_dir.name[:2]) if chap_dir.name[:2].isdigit() else 0
            }
            
        for rel, node in folder_nodes.items():
            if rel == chap_root_rel:
                continue
                
            curr = rel.parent
            while curr != Path("."):
                if curr in folder_nodes:
                    folder_nodes[curr]["children"].append(node)
                    break
                if curr == chap_root_rel:
                    folder_nodes[curr]["children"].append(node)
                    break
                curr = curr.parent

        root_node = folder_nodes[chap_root_rel]
        
        def sort_children(n):
            n["children"].sort(key=lambda x: x["order_index"])
            for c in n["children"]:
                sort_children(c)
                
        sort_children(root_node)
        structured_content.append(root_node)
        
    conn = db._get_connection()
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA journal_mode = MEMORY;")
    conn.commit()
    conn.close()

    try:
        try:
            existing_book = find_existing_book(db, title, book_folder)
        except AmbiguousBookError as e:
            print(f"[SKIP] Ambiguous match: {e}")
            return 0, 0
            
        existing_id = existing_book["id"] if existing_book else None
        
        book_id = save_or_update_book(
            db=db,
            title=title,
            author=author,
            source_path=source_path,
            published_year=published_year,
            site_category=site_category,
            structured_content=structured_content,
            existing_book_id=existing_id
        )
        if book_id != -1:
            return len(content_files), 1
        return 0, -1
    finally:
        conn = db._get_connection()
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.commit()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Bulk import extracted ebooks to DB.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be imported without DB changes.")
    parser.add_argument("--book", type=str, help="Import a specific book by folder name or path.")
    parser.add_argument("--folder", type=str, help="Path to a specific book folder to import directly.")
    parser.add_argument("--category", type=str, default="plant", help="Category to assign (default: plant).")
    parser.add_argument("--verbose", action="store_true", help="Print verbose progress.")
    parser.add_argument("--lib-dir", type=str, default=r"D:\Extracted-EBOOKS", help="Path to EBOOKS directory.")
    
    args = parser.parse_args()
    db = DatabaseManager()
    
    # Handle direct single folder import if --folder or if --book points to an existing directory
    single_folder = None
    if args.folder and Path(args.folder).is_dir():
        single_folder = Path(args.folder)
    elif args.book and Path(args.book).is_dir():
        single_folder = Path(args.book)
        
    if single_folder:
        print(f"Importing single folder: {single_folder}")
        if args.dry_run:
            print("DRY RUN MODE - No DB changes will be made")
        is_existing = book_already_imported(db, single_folder)
        articles_count, status = process_book(single_folder, args.category, db, args.dry_run)
        action_tag = "UPDATED" if is_existing else "OK"
        if status == 1:
            print(f"Success: {single_folder.name} ({args.category}) — {articles_count} articles ... {action_tag}")
        elif status == -1:
            print(f"Error importing {single_folder.name}")
        elif status == 0:
            print(f"Skipped {single_folder.name}")
        return

    lib_path = Path(args.lib_dir)
    json_path = lib_path / "_classification.json"
    
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            full_json = json.load(f)
            classification = full_json.get('books', [])
    else:
        # Fallback if no _classification.json: list all directories in lib_dir
        classification = [{'folder': f.name, 'category': args.category} for f in sorted(lib_path.iterdir()) if f.is_dir()]
        
    books_imported = 0
    books_updated = 0
    books_skipped = 0
    total_articles = 0
    start_time = time.time()
    
    print(f"Starting import from {lib_path}")
    if args.dry_run:
        print("DRY RUN MODE - No DB changes will be made")
    print("-" * 40)
    
    total_keys = len(classification)
    idx = 0
    for entry in classification:
        folder_name = entry.get('folder', '')
        cat = entry.get('category', args.category)
        if args.book and args.book.lower() not in folder_name.lower():
            continue
            
        idx += 1
        book_folder = lib_path / folder_name
        
        if cat.lower() == "off":
            if args.verbose or args.book:
                 print(f"[{idx}/{total_keys}] {folder_name} (off) — SKIPPED (off-topic)")
            books_skipped += 1
            continue
            
        if not book_folder.exists():
             if args.verbose or args.book:
                 print(f"[{idx}/{total_keys}] {folder_name} ({cat}) — SKIPPED (Folder doesn't exist)")
             continue
             
        is_existing = book_already_imported(db, book_folder)
        articles_count, status = process_book(book_folder, cat, db, args.dry_run)
        
        if status == 1:
            action_tag = "UPDATED" if is_existing else "OK"
            print(f"[{idx}/{total_keys}] {folder_name} ({cat}) — {articles_count} articles ... {action_tag}")
            if is_existing:
                books_updated += 1
            else:
                books_imported += 1
            total_articles += articles_count
        elif status == -1:
            print(f"[{idx}/{total_keys}] {folder_name} ({cat}) — ERROR importing.")
        elif status == 0:
            books_skipped += 1
            
    duration = time.time() - start_time
    mins = int(duration // 60)
    secs = int(duration % 60)
    
    print("\n" + "-" * 40)
    print("Import complete")
    print(f"  Books imported : {books_imported} (new) + {books_updated} (updated)")
    print(f"  Books skipped  : {books_skipped}")
    print(f"  Total articles : {total_articles:,}")
    print(f"  Duration       : {mins}m {secs}s")
    print("-" * 40)


if __name__ == "__main__":
    main()
