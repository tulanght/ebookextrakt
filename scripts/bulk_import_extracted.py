# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: scripts/bulk_import_extracted.py
# Version: 1.0.0
# Author: Antigravity
# Description: Bulk imports ebooks from filesystem into SQLite database with FTS mapping.
# --------------------------------------------------------------------------------

import argparse
import sys
import os
import json
import re
import yaml
import time
from pathlib import Path

# Add project root to path so we can import src
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.extract_app.core.database import DatabaseManager

def parse_content_md(filepath: Path) -> tuple[dict, str]:
    """Returns (frontmatter_dict, body_text)"""
    try:
        text = filepath.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return {}, ""
        
    parts = text.split('---', 2)
    if len(parts) < 3:
        return {}, text
    
    fm_text = parts[1]
    body = parts[2].strip()
    
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        fm = {}
        
    # Lọc noise trong body (remove custom footer)
    body = re.sub(r'\n+> \*\*Nguồn:\*\*.*$', '', body, flags=re.MULTILINE).strip()
    return fm, body

def get_chapter_folder(content_md_path: Path, book_root: Path) -> Path:
    """Trả về second-level subfolder (chapter) chứa file này."""
    relative = content_md_path.relative_to(book_root)
    if len(relative.parts) <= 1:
        return book_root
    return book_root / relative.parts[0]

def book_already_imported(db: DatabaseManager, book_folder: Path) -> bool:
    """Check bằng source_path."""
    conn = db._get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM books WHERE source_path = ?", (str(book_folder),))
    result = c.fetchone()
    conn.close()
    return result is not None

def process_book(book_folder: Path, classification_cat: str, db: DatabaseManager, dry_run: bool = False) -> tuple[int, int]:
    """Process a single book folder. Returns (articles_count: int, status: int). status: 0=skip, 1=success, -1=error."""
    if book_already_imported(db, book_folder):
        return 0, 0
        
    content_files = list(book_folder.rglob("content.md"))
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
            sec_idx = fm.get("section_index", 0)
            
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
        book_id = db.save_book_batch(title, author, source_path, "", structured_content, published_year)
        if book_id != -1:
            conn = db._get_connection()
            conn.execute("UPDATE books SET site_category = ? WHERE id = ?", (site_category, book_id))
            conn.commit()
            conn.close()
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
    parser.add_argument("--book", type=str, help="Import a specific book by folder name.")
    parser.add_argument("--verbose", action="store_true", help="Print verbose progress.")
    parser.add_argument("--lib-dir", type=str, default=r"D:\Extracted-EBOOKS", help="Path to EBOOKS directory.")
    
    args = parser.parse_args()
    
    lib_path = Path(args.lib_dir)
    json_path = lib_path / "_classification.json"
    
    if not json_path.exists():
        print(f"Error: {json_path} not found.")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        full_json = json.load(f)
        classification = full_json.get('books', {})
        
    db = DatabaseManager()
    
    books_imported = 0
    books_skipped = 0
    books_skipped_db = 0
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
        cat = entry.get('category', 'off')
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
             
        if book_already_imported(db, book_folder):
            books_skipped_db += 1
            if args.verbose or args.book:
                 print(f"[{idx}/{total_keys}] {folder_name} ({cat}) — SKIPPED (Already in DB)")
            continue
            
        articles_count, status = process_book(book_folder, cat, db, args.dry_run)
        
        if status == 1:
            print(f"[{idx}/{total_keys}] {folder_name} ({cat}) — {articles_count} articles ... OK")
            books_imported += 1
            total_articles += articles_count
        elif status == -1:
            print(f"[{idx}/{total_keys}] {folder_name} ({cat}) — ERROR importing.")
            
    if not args.dry_run and books_imported > 0:
        print("\nRebuilding FTS5 index...")
        count = db.rebuild_fts_index()
        print(f"FTS5: {count:,} articles indexed.")
    else:
        count = 0
        
    duration = time.time() - start_time
    mins = int(duration // 60)
    secs = int(duration % 60)
    
    print("\n" + "-" * 40)
    print("Import complete")
    print(f"  Books imported : {books_imported}")
    print(f"  Books skipped  : {books_skipped} (off) + {books_skipped_db} (already in DB)")
    print(f"  Total articles : {total_articles:,}")
    if not args.dry_run:
        print(f"  FTS5 indexed   : {count:,} (is_leaf only)")
    print(f"  Duration       : {mins}m {secs}s")
    print("-" * 40)

if __name__ == "__main__":
    main()
