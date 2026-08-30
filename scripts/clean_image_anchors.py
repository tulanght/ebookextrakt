# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: scripts/clean_image_anchors.py
# Version: 1.0.0
# Author: Antigravity
# Description: Cleans [Image Anchor: ...] tags from articles.content_text in SQLite DB.
# --------------------------------------------------------------------------------

import re
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.extract_app.core.database import DatabaseManager


def clean_image_anchors(db_path: str = None) -> None:
    """
    Cleans [Image Anchor: ...] tags from articles.content_text in SQLite database.

    Args:
        db_path: Optional path to SQLite database file.
    """
    db = DatabaseManager(db_path=db_path) if db_path else DatabaseManager()
    conn = db._get_connection()
    cursor = conn.cursor()

    try:
        # 1. Print COUNT(*) before
        cursor.execute("SELECT COUNT(*) FROM articles")
        count_before = cursor.fetchone()[0]
        print(f"COUNT(*) FROM articles (TRUOC): {count_before}")

        # 2. SELECT articles with Image Anchor tags
        cursor.execute("SELECT id, content_text FROM articles WHERE content_text LIKE '%[Image Anchor:%'")
        rows = cursor.fetchall()
        print(f"So dong can xu ly: {len(rows)}")

        # 3. Strip tags and update content_text and word_count
        anchor_pattern = re.compile(r'\[Image Anchor:[^\]]*\]')
        updated_count = 0

        for row in rows:
            article_id = row[0]
            content_text = row[1] or ""
            cleaned_text = anchor_pattern.sub('', content_text)
            word_count = len(cleaned_text.split()) if cleaned_text else 0

            cursor.execute(
                "UPDATE articles SET content_text = ?, word_count = ? WHERE id = ?",
                (cleaned_text, word_count, article_id)
            )
            updated_count += 1

        conn.commit()
        print(f"Da cap nhat thanh cong: {updated_count} dong")

        # 4. Print COUNT(*) after
        cursor.execute("SELECT COUNT(*) FROM articles")
        count_after = cursor.fetchone()[0]
        print(f"COUNT(*) FROM articles (SAU): {count_after}")

        # 5. Check remaining tags in DB
        cursor.execute("SELECT COUNT(*) FROM articles WHERE content_text LIKE '%[Image Anchor:%'")
        remaining = cursor.fetchone()[0]
        print(f"So dong con chua [Image Anchor:] trong DB: {remaining}")

        if count_before != 95628 or count_after != 95628:
            print(f"CANH BAO: COUNT(*) khong bang 95628! (Truoc: {count_before}, Sau: {count_after})")
        else:
            print("XAC NHAN: COUNT(*) giu nguyen 95628 ca truoc va sau khi xu ly.")

    finally:
        conn.close()


if __name__ == "__main__":
    clean_image_anchors()
