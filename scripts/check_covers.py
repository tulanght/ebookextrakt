import sqlite3
from pathlib import Path
from PIL import Image

conn = sqlite3.connect("user_data/extract.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT id, title, cover_path FROM books")
for r in c.fetchall():
    cover = r["cover_path"] or ""
    exists = Path(cover).exists() if cover else False
    size = ""
    if exists:
        img = Image.open(cover)
        size = f"{img.size[0]}x{img.size[1]}"
    print(f"  ID={r['id']} | title={r['title']} | cover_exists={exists} | size={size}")
    print(f"    path: {cover}")
conn.close()
