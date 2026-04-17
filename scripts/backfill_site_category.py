"""
Backfills the site_category into content.md files and the database.
Uses _classification.json as the source of truth.
"""
import sys
import json
import re
from pathlib import Path

# Add src to python path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from extract_app.core.database import DatabaseManager

EXTENDED_EBOOKS_DIR = Path(r"D:\Extracted-EBOOKS")
CLASSIFICATION_FILE = EXTENDED_EBOOKS_DIR / "_classification.json"

def get_classifications():
    if not CLASSIFICATION_FILE.exists():
        print(f"Error: {CLASSIFICATION_FILE} not found.")
        sys.exit(1)
        
    with open(CLASSIFICATION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Build lookup dict mapping folder -> category
    cats = {}
    for book in data.get("books", []):
        cats[book["folder"]] = book.get("category", "unclassified")
    return cats

def update_frontmatter(file_path: Path, new_category: str) -> bool:
    """
    Updates the 'site_category' in YAML frontmatter.
    Returns True if modified, False if unchanged.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        
        # Check if frontmatter exists
        if content.startswith("---"):
            end_idx = content.find("\n---\n", 3)
            if end_idx != -1:
                frontmatter = content[3:end_idx]
                body = content[end_idx+5:]
                
                # Check if site_category already exists
                has_site_cat = re.search(r"^site_category:(.*)$", frontmatter, flags=re.MULTILINE)
                
                if has_site_cat:
                    current_val = has_site_cat.group(1).strip()
                    if current_val == new_category:
                        return False # No change needed
                    # Replace existing
                    new_frontmatter = re.sub(
                        r"^site_category:(.*)$", 
                        f"site_category: {new_category}", 
                        frontmatter, 
                        flags=re.MULTILINE
                    )
                else:
                    # Append new
                    new_frontmatter = frontmatter + f"\nsite_category: {new_category}"
                    
                new_content = f"---{new_frontmatter}\n---\n{body}"
                file_path.write_text(new_content, encoding="utf-8")
                return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False

def main():
    print("Loading classifications...")
    classifications = get_classifications()
    print(f"Loaded {len(classifications)} entries from classification.json.")
    
    files_updated = 0
    files_skipped = 0
    not_found_in_class = set()
    
    print("Updating content.md files...")
    # Find all content.md files
    for md_file in EXTENDED_EBOOKS_DIR.rglob("content.md"):
        # Relies on the folder structure: D:\Extracted-EBOOKS\BookName\...
        rel_path = md_file.relative_to(EXTENDED_EBOOKS_DIR)
        book_folder = rel_path.parts[0]
        
        # We might have books that have prefixes or suffix differences, so let's match closely
        # Actually _classification.json was built out of this folder, so exact match should work mostly
        site_category = "unclassified"
        # Try exact match
        if book_folder in classifications:
            site_category = classifications[book_folder]
        else:
            # Fallback: substring match just in case
            matched = False
            for k, v in classifications.items():
                if book_folder.startswith(k) or k.startswith(book_folder):
                    site_category = v
                    matched = True
                    break
            
            if not matched:
                not_found_in_class.add(book_folder)
                
        if update_frontmatter(md_file, site_category):
            files_updated += 1
        else:
            files_skipped += 1
            
    print(f"\nFiles updated: {files_updated}")
    print(f"Files skipped (already correct): {files_skipped}")
    if not_found_in_class:
        print(f"Books without classification: {len(not_found_in_class)}")
        for b in list(not_found_in_class)[:5]:
            print(f"  - {b}")
            
    print("\nUpdating Database...")
    db = DatabaseManager()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    # Get all books from DB
    cursor.execute("SELECT id, source_path FROM books")
    db_books = cursor.fetchall()
    
    db_updated = 0
    for row in db_books:
        book_id = row['id']
        source_path = row['source_path']
        
        # Extract the likely folder name from the source path
        # Assuming source_path is the original EPUB/PDF name
        source_name = Path(source_path).stem
        
        db_site_category = "unclassified"
        for folder_name, cat in classifications.items():
            if folder_name == source_name or folder_name.startswith(source_name) or source_name.startswith(folder_name):
                db_site_category = cat
                break
                
        cursor.execute("UPDATE books SET site_category = ? WHERE id = ?", (db_site_category, book_id))
        db_updated += 1
        
    conn.commit()
    conn.close()
    
    print(f"Database books updated: {db_updated}")
    print("Done!")

if __name__ == "__main__":
    main()
