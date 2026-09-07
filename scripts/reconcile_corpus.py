# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: scripts/reconcile_corpus.py
# Version: 1.0.0
# Author: Antigravity
# Description: Corpus reconciliation tool comparing counts across content.txt,
#              content.md, extract.db articles, and QMD index documents.
# --------------------------------------------------------------------------------

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.extract_app.shared.constants import MIN_ARTICLE_BYTES


def normalize_title(t: str) -> str:
    """Normalizes a title for deduplication and matching comparison.

    Strips leading numeric indices (e.g. '01 - '), punctuation, whitespace,
    and converts to lowercase.

    Args:
        t: Raw title or folder name string.

    Returns:
        Normalized title string.
    """
    if not t:
        return ""
    t = re.sub(r"^\d+\s*-\s*", "", t)
    return re.sub(r"[\s\-_'\"`\u2018\u2019\u201c\u201d.,:;!?()]", "", t).lower()


def scan_disk_files(root_dir: Path) -> Dict[str, any]:
    """Scans the given root directory for content.txt and content.md files.

    Categorizes files into valid (size >= MIN_ARTICLE_BYTES) and skipped (< MIN_ARTICLE_BYTES).

    Args:
        root_dir: Root Path of the corpus.

    Returns:
        Dictionary containing counts and lists of file paths.
    """
    txt_all: List[Path] = []
    txt_valid: List[Path] = []
    txt_skipped: List[Path] = []

    md_all: List[Path] = []
    md_valid: List[Path] = []
    md_skipped: List[Path] = []

    book_folders: Set[Path] = set()

    def _walk(entry_path: Path, current_book_folder: Optional[Path]):
        try:
            with os.scandir(entry_path) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        bf = current_book_folder if current_book_folder else Path(entry.path)
                        _walk(Path(entry.path), bf)
                    elif entry.is_file(follow_symlinks=False):
                        if entry.name == "content.txt":
                            p = Path(entry.path)
                            txt_all.append(p)
                            if current_book_folder:
                                book_folders.add(current_book_folder)
                            try:
                                sz = entry.stat().st_size
                                if sz >= MIN_ARTICLE_BYTES:
                                    txt_valid.append(p)
                                else:
                                    txt_skipped.append(p)
                            except OSError:
                                txt_skipped.append(p)
                        elif entry.name == "content.md":
                            p = Path(entry.path)
                            md_all.append(p)
                            try:
                                sz = entry.stat().st_size
                                if sz >= MIN_ARTICLE_BYTES:
                                    md_valid.append(p)
                                else:
                                    md_skipped.append(p)
                            except OSError:
                                md_skipped.append(p)
        except OSError:
            pass

    try:
        with os.scandir(root_dir) as it:
            for entry in it:
                if entry.is_dir(follow_symlinks=False):
                    bf = Path(entry.path)
                    _walk(bf, bf)
                elif entry.is_file(follow_symlinks=False):
                    if entry.name == "content.txt":
                        p = Path(entry.path)
                        txt_all.append(p)
                        try:
                            if entry.stat().st_size >= MIN_ARTICLE_BYTES:
                                txt_valid.append(p)
                            else:
                                txt_skipped.append(p)
                        except OSError:
                            txt_skipped.append(p)
                    elif entry.name == "content.md":
                        p = Path(entry.path)
                        md_all.append(p)
                        try:
                            if entry.stat().st_size >= MIN_ARTICLE_BYTES:
                                md_valid.append(p)
                            else:
                                md_skipped.append(p)
                        except OSError:
                            md_skipped.append(p)
    except OSError:
        pass

    return {
        "txt_total": len(txt_all),
        "txt_valid": len(txt_valid),
        "txt_skipped": len(txt_skipped),
        "txt_valid_paths": txt_valid,
        "txt_skipped_paths": txt_skipped,
        "md_total": len(md_all),
        "md_valid": len(md_valid),
        "md_skipped": len(md_skipped),
        "md_valid_paths": md_valid,
        "md_skipped_paths": md_skipped,
        "book_folders": sorted(list(book_folders), key=lambda x: x.name),
    }


def query_db_articles(db_path: Path, root_dir: Path, book_folders: List[Path]) -> Dict[str, any]:
    """Queries extract.db for articles belonging to the books in root_dir.

    Args:
        db_path: Path to extract.db.
        root_dir: Root directory of the corpus.
        book_folders: List of book folder paths discovered under root_dir.

    Returns:
        Dictionary containing matched books, total articles, and leaf articles.
    """
    if not db_path.exists():
        return {
            "exists": False,
            "matched_books": 0,
            "total_folders": len(book_folders),
            "total_articles": 0,
            "leaf_articles": 0,
            "unmatched_folders": [bf.name for bf in book_folders],
        }

    conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    c = conn.cursor()

    db_books = c.execute("SELECT id, title, source_path, site_category FROM books").fetchall()

    # Match each book folder against DB
    matched_book_ids: Set[int] = set()
    unmatched_folders: List[str] = []

    # Also consider all direct subdirectories in root_dir if book_folders is empty
    target_folders = book_folders if book_folders else [p for p in root_dir.iterdir() if p.is_dir()]

    for bf in target_folders:
        norm_name = normalize_title(bf.name)
        matched_id = None
        for bid, title, source_path, _ in db_books:
            if norm_name and norm_name == normalize_title(title):
                matched_id = bid
                break
            if source_path:
                source_stem_norm = normalize_title(Path(source_path).stem)
                if norm_name and norm_name == source_stem_norm:
                    matched_id = bid
                    break
                try:
                    if Path(source_path).resolve() == bf.resolve():
                        matched_id = bid
                        break
                except Exception:
                    pass

        if matched_id is not None:
            matched_book_ids.add(matched_id)
        else:
            unmatched_folders.append(bf.name)

    total_articles = 0
    leaf_articles = 0

    if matched_book_ids:
        placeholders = ",".join("?" * len(matched_book_ids))
        total_articles = c.execute(
            f"""
            SELECT COUNT(*) FROM articles a 
            JOIN chapters ch ON a.chapter_id = ch.id 
            WHERE ch.book_id IN ({placeholders})
        """,
            list(matched_book_ids),
        ).fetchone()[0]

        leaf_articles = c.execute(
            f"""
            SELECT COUNT(*) FROM articles a 
            JOIN chapters ch ON a.chapter_id = ch.id 
            WHERE ch.book_id IN ({placeholders}) AND a.is_leaf = 1
        """,
            list(matched_book_ids),
        ).fetchone()[0]

    conn.close()

    return {
        "exists": True,
        "matched_books": len(matched_book_ids),
        "total_folders": len(target_folders),
        "total_articles": total_articles,
        "leaf_articles": leaf_articles,
        "unmatched_folders": unmatched_folders,
    }


def query_qmd_documents(qmd_path: Path, root_dir: Path) -> Dict[str, any]:
    """Queries QMD index.sqlite for documents belonging to root_dir collection.

    Args:
        qmd_path: Path to QMD index.sqlite.
        root_dir: Root directory of the corpus.

    Returns:
        Dictionary containing collection names and document counts.
    """
    if not qmd_path.exists():
        return {
            "exists": False,
            "matched_collections": [],
            "documents_count": 0,
        }

    conn = sqlite3.connect(f"file:{qmd_path.resolve()}?mode=ro", uri=True)
    c = conn.cursor()

    collections = c.execute("SELECT name, path FROM store_collections").fetchall()
    matched_colls: List[str] = []

    for cname, cpath in collections:
        if cpath:
            try:
                if Path(cpath).resolve() == root_dir.resolve():
                    matched_colls.append(cname)
            except Exception:
                pass

    if not matched_colls:
        # Fallback: substring matching between collection name and root_dir name
        for cname, _ in collections:
            if cname.lower() in root_dir.name.lower() or root_dir.name.lower() in cname.lower():
                matched_colls.append(cname)

    doc_count = 0
    for cname in matched_colls:
        count = c.execute(
            "SELECT COUNT(*) FROM documents WHERE collection = ?", (cname,)
        ).fetchone()[0]
        doc_count += count

    conn.close()

    return {
        "exists": True,
        "matched_collections": matched_colls,
        "documents_count": doc_count,
    }


def reconcile(
    root_dir: Path,
    db_path: Optional[Path] = None,
    qmd_path: Optional[Path] = None,
    verbose: bool = False,
) -> int:
    """Performs full reconciliation across disk, DB, and QMD index.

    Args:
        root_dir: Corpus root directory path.
        db_path: Path to extract.db.
        qmd_path: Path to QMD index.sqlite.
        verbose: If True, prints verbose details of mismatches.

    Returns:
        0 if all counts reconcile, 1 if there is a mismatch.
    """
    if not root_dir.exists():
        print(f"[ERROR] Directory '{root_dir}' does not exist.")
        return 1

    if db_path is None:
        db_path = project_root / "user_data" / "extract.db"

    if qmd_path is None:
        qmd_path = Path(os.path.expanduser("~/.cache/qmd/index.sqlite"))

    print("=" * 70)
    print(f"CORPUS RECONCILIATION AUDIT: {root_dir}")
    print("=" * 70)
    print(f"Threshold MIN_ARTICLE_BYTES : {MIN_ARTICLE_BYTES} bytes\n")

    # 1 & 2. Scan disk files
    print("[1/3] Scanning disk files...")
    disk_data = scan_disk_files(root_dir)

    # 3. Query DB
    print("[2/3] Querying extract.db...")
    db_data = query_db_articles(db_path, root_dir, disk_data["book_folders"])

    # 4. Query QMD
    print("[3/3] Querying QMD index...")
    qmd_data = query_qmd_documents(qmd_path, root_dir)

    print("\n" + "-" * 70)
    print("RECONCILIATION SUMMARY MATRIX")
    print("-" * 70)
    print(f"  1. Disk content.txt : {disk_data['txt_valid']:>6} valid  ({disk_data['txt_total']:>6} total, -{disk_data['txt_skipped']} skipped <{MIN_ARTICLE_BYTES}B)")
    print(f"  2. Disk content.md  : {disk_data['md_valid']:>6} valid  ({disk_data['md_total']:>6} total, -{disk_data['md_skipped']} skipped <{MIN_ARTICLE_BYTES}B)")
    
    if db_data["exists"]:
        print(f"  3. Database articles: {db_data['leaf_articles']:>6} leaf   ({db_data['total_articles']:>6} total, {db_data['matched_books']}/{db_data['total_folders']} books matched)")
    else:
        print(f"  3. Database articles: [DB NOT FOUND at {db_path}]")

    if qmd_data["exists"] and qmd_data["matched_collections"]:
        colls_str = ", ".join(qmd_data["matched_collections"])
        print(f"  4. QMD Index docs   : {qmd_data['documents_count']:>6} docs   (collection: {colls_str})")
    elif qmd_data["exists"]:
        print(f"  4. QMD Index docs   :      0 docs   (no collection mapped for {root_dir.name})")
    else:
        print(f"  4. QMD Index docs   : [QMD NOT FOUND at {qmd_path}]")

    print("-" * 70)

    # Discrepancy checks
    mismatches: List[str] = []

    # Check 1: content.txt vs content.md
    if disk_data["txt_valid"] != disk_data["md_valid"]:
        diff = disk_data["txt_valid"] - disk_data["md_valid"]
        mismatches.append(
            f"[MISMATCH] Disk txt vs md: {disk_data['txt_valid']} valid content.txt vs {disk_data['md_valid']} valid content.md (diff: {diff:+d}). "
            f"{'Need to run markdown_exporter.py' if diff > 0 else 'Unexpected extra md files'}."
        )

    # Check 2: Disk content.md vs DB leaf articles (if DB is populated for this corpus)
    if db_data["exists"]:
        if db_data["matched_books"] < db_data["total_folders"]:
            unmatched_count = db_data["total_folders"] - db_data["matched_books"]
            mismatches.append(
                f"[MISMATCH] DB Book Coverage: Only {db_data['matched_books']}/{db_data['total_folders']} book folders matched in DB ({unmatched_count} books missing/unmatched)."
            )
        if db_data["leaf_articles"] != disk_data["md_valid"]:
            diff = disk_data["md_valid"] - db_data["leaf_articles"]
            mismatches.append(
                f"[MISMATCH] Disk md vs DB leaf articles: {disk_data['md_valid']} valid content.md vs {db_data['leaf_articles']} DB leaf articles (diff: {diff:+d})."
            )

    # Check 3: QMD docs vs Disk content.md (if QMD collection exists)
    if qmd_data["matched_collections"]:
        if qmd_data["documents_count"] != disk_data["md_valid"]:
            diff = disk_data["md_valid"] - qmd_data["documents_count"]
            mismatches.append(
                f"[MISMATCH] Disk md vs QMD docs: {disk_data['md_valid']} valid content.md vs {qmd_data['documents_count']} QMD documents (diff: {diff:+d})."
            )

    if mismatches:
        print("\n*** DISCREPANCY AUDIT FAILED ***")
        for m in mismatches:
            print(f"  * {m}")

        if verbose or (db_data["exists"] and db_data["unmatched_folders"] and len(db_data["unmatched_folders"]) <= 20):
            if db_data["unmatched_folders"]:
                print("\nUnmatched book folders in DB:")
                for ub in db_data["unmatched_folders"][:20]:
                    print(f"    - {ub}")
                if len(db_data["unmatched_folders"]) > 20:
                    print(f"    ... and {len(db_data['unmatched_folders']) - 20} more.")

        print("\nReconciliation Result: FAILED (exit code 1)")
        return 1
    else:
        print("\n=== ALL 4 NUMBERS RECONCILED PERFECTLY ===")
        print("Reconciliation Result: PASSED (exit code 0)")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Reconcile corpus numbers across content.txt, content.md, extract.db, and QMD index."
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        required=True,
        help="Root directory of the corpus (e.g. 'D:\\Garden Home and Plants' or 'D:\\Extracted-EBOOKS').",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Path to extract.db SQLite file (defaults to user_data/extract.db).",
    )
    parser.add_argument(
        "--qmd",
        type=str,
        default=None,
        help="Path to QMD index.sqlite (defaults to ~/.cache/qmd/index.sqlite).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print verbose details of discrepancies.",
    )

    args = parser.parse_args()

    # Force UTF-8 encoding on stdout for Windows terminal compatibility
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    root_dir = Path(args.dir).resolve()
    db_path = Path(args.db).resolve() if args.db else None
    qmd_path = Path(args.qmd).resolve() if args.qmd else None

    exit_code = reconcile(root_dir, db_path, qmd_path, args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
