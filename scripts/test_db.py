# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: scripts/test_db.py
# Description: Verifies sqlite database functionality.
# --------------------------------------------------------------------------------

import sys
import os
import shutil
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from extract_app.core.database import DatabaseManager
    
    TEST_DB = "test_data/test.db"
    if Path(TEST_DB).exists():
        os.remove(TEST_DB)
        
    print("Initializing Database...")
    db = DatabaseManager(db_path=TEST_DB)
    
    print("1. Adding Book...")
    book_id = db.add_book("Test Book", "Author A", "C:/Books/test.epub")
    assert book_id > 0
    print(f"   -> Book ID: {book_id}")
    
    print("2. Adding Chapter...")
    chap_id = db.add_chapter(book_id, "Chapter 1", 0)
    assert chap_id > 0
    print(f"   -> Chapter ID: {chap_id}")
    
    print("3. Adding Article...")
    art_id = db.add_article(chap_id, "Introduction", "Hello World content.", 0)
    assert art_id > 0
    print(f"   -> Article ID: {art_id}")
    
    print("4. Adding Image...")
    db.add_image(art_id, "img/test.jpg", "A test image")
    
    print("5. Retrieving Data...")
    books = db.get_all_books()
    assert len(books) == 1
    assert books[0]['title'] == "Test Book"
    print("   -> Retrieval Success")
    
    # Cleanup
    if Path(TEST_DB).exists():
        os.remove(TEST_DB)
    if Path("test_data").exists():
        os.rmdir("test_data")
        
    print("ALL TESTS PASSED.")

except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
