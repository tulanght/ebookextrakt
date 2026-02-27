"""Diagnostic: check cover images stored in the database."""
import sqlite3
from pathlib import Path
from PIL import Image

DB_PATH = Path("user_data/extract.db")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT id, title, cover_path, published_year FROM books")
books = cursor.fetchall()

print(f"Found {len(books)} books in DB\n")

for book in books:
    cover_path = book['cover_path'] or ""
    print(f"Book #{book['id']}: {book['title']}")
    print(f"  Year: {book['published_year']}")
    print(f"  Cover path: {cover_path}")
    
    if cover_path and Path(cover_path).exists():
        img = Image.open(cover_path)
        print(f"  Cover size: {img.size} (WxH)")
        print(f"  Cover mode: {img.mode}")
        print(f"  File size: {Path(cover_path).stat().st_size} bytes")
    elif cover_path:
        print(f"  ⚠️ Cover file DOES NOT EXIST at path!")
    else:
        print(f"  ⚠️ No cover path stored")
    print()

conn.close()
