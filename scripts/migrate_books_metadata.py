import sqlite3
import re
from pathlib import Path

DB_PATH = Path("user_data/extract.db")

def migrate_metadata():
    if not DB_PATH.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, published_year FROM books")
    books = cursor.fetchall()

    updated_count = 0
    for book in books:
        book_id = book['id']
        old_title = book['title']
        old_year = book['published_year']
        
        new_title = old_title
        new_year = old_year

        # Clean title
        new_title = re.sub(r'\s*\(Z-Library\)', '', new_title, flags=re.IGNORECASE)
        new_title = re.sub(r'_(pdf|epub|mobi)$', '', new_title, flags=re.IGNORECASE)
        new_title = re.sub(r'\.(pdf|epub|mobi)$', '', new_title, flags=re.IGNORECASE)
        
        # Extract year if empty
        if not new_year:
            year_match = re.search(r'\((\d{4})\)', new_title)
            if year_match:
                new_year = year_match.group(1)
                new_title = re.sub(r'\s*\(\d{4}\)', '', new_title).strip()
        
        new_title = new_title.strip()

        if new_title != old_title or new_year != old_year:
            print(f"Updating Book ID {book_id}:")
            print(f"  Old: {old_title} | Year: {old_year}")
            print(f"  New: {new_title} | Year: {new_year}")
            
            cursor.execute(
                "UPDATE books SET title = ?, published_year = ? WHERE id = ?",
                (new_title, new_year, book_id)
            )
            updated_count += 1

    conn.commit()
    conn.close()
    print(f"Migration complete. Updated {updated_count} books.")

if __name__ == "__main__":
    migrate_metadata()
