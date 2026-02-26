
import sqlite3
import shutil
import os
import sys
from pathlib import Path

# Add src to path to import parsers
sys.path.append(os.path.abspath("src"))

from extract_app.core.epub_parser import parse_epub
# Note: pdf_parser doesn't support cover extraction well yet, we focus on EPUB
# actually pdf_parser *does* extract some things but let's stick to standard flow logic

DB_PATH = "user_data/extract.db"
BASE_DIR = Path("user_data/books") # Assuming this is where books are saved?
# Wait, storage_handler.save_as_folders uses base_path passed from main_window.
# main_window passes 'target_dir' which users select. 
# We might not know where they saved it!
# BUT the DB has 'cover_path'. If it's empty, we need to fix it.
# We CANNOT know where the book content was saved unless we stored 'output_path' in DB.
# Database schema: books (id, title, author, source_path, cover_path, category, tags, added_date)
# We do NOT store the output directory of the extracted content in the DB.
# However, we can try to save the cover to `user_data/covers/{id}.webp` and update DB.
# The LibraryView loads cover from `cover_path`.
# So we can centralize covers!

COVER_DIR = Path("user_data/covers")
COVER_DIR.mkdir(parents=True, exist_ok=True)

def repair_covers():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, source_path, cover_path FROM books")
    books = cursor.fetchall()
    
    print(f"Found {len(books)} books. Checking covers...")
    
    for book in books:
        book_id = book['id']
        title = book['title']
        source = book['source_path']
        current_cover = book['cover_path']
        
        # Check if needs repair
        needs_repair = False
        if not current_cover:
            needs_repair = True
        elif not os.path.exists(current_cover):
             print(f"Cover path missing: {current_cover}")
             needs_repair = True
             
        if not needs_repair:
            continue
            
        print(f"Reparing cover for: {title}...")
        
        if not source or not os.path.exists(source):
            print(f"  Source file not found: {source}")
            continue
            
        # Extract cover
        try:
            # We use a simplified extraction or just reuse parse_epub but ignore content
            # parsing whole epub is slow.
            # Let's use logic from epub_parser quickly here?
            # Or just call parse_epub and ignore content (easiest for now)
            
            # Since we can't easily import just the cover logic without refactoring, 
            # and I don't want to break existing code, 
            # I will attempt to use `ebooklib` directly here if possible, 
            # OR just rely on the fact that `parse_epub` might work.
            
            # Actually, let's copy the cover extraction logic minimally.
            from ebooklib import epub
            from bs4 import BeautifulSoup
            
            book_obj = epub.read_epub(source)
            cover_data = None
            cover_ext = ".webp"
            
            # 1. Metadata
            # ... (Logic from epub_parser)
            images = list(book_obj.get_items_of_type(9)) # 9 = image
            # Metadata finding...
            # Simplified: Just grab the first thing looking like a cover
            
            cover_item = None
            # Try ID
            for x in ['cover', 'cover-image', 'coverimage']:
                cover_item = book_obj.get_item_with_id(x)
                if cover_item: break
            
            if not cover_item:
                 # Try filename
                 for item in book_obj.get_items():
                     if 'cover' in item.get_name().lower() and item.media_type.startswith('image/'):
                         cover_item = item
                         break
            
            if cover_item:
                cover_content = cover_item.get_content()
                cover_name = f"cover_{book_id}.webp"
                dest_path = COVER_DIR / cover_name
                
                # Convert to webp
                from PIL import Image
                import io
                
                img = Image.open(io.BytesIO(cover_content))
                img.save(dest_path, "WEBP")
                
                print(f"  Extracted cover to: {dest_path}")
                
                # Update DB
                cursor.execute("UPDATE books SET cover_path = ? WHERE id = ?", (str(dest_path), book_id))
                conn.commit()
                print("  DB Updated.")
            else:
                print("  No cover found in EPUB.")
                
        except Exception as e:
            print(f"  Failed to repair: {e}")

    conn.close()
    print("Repair complete.")

if __name__ == "__main__":
    repair_covers()
