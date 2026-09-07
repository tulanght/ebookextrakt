import sys
import os
from pathlib import Path

# Thêm thư mục src vào sys.path để import
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from extract_app.core.database import DatabaseManager

def main():
    db = DatabaseManager()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    # In ra path cũ để debug
    cursor.execute("SELECT id, title, source_path FROM books LIMIT 5")
    rows = cursor.fetchall()
    
    print("=== BEFORE UPDATE ===")
    for r in rows:
        print(f"Book {r['id']}: {r['source_path']}")
        
    print("\nExecuting update...")
    
    # Update backslash
    cursor.execute("""
        UPDATE books 
        SET source_path = REPLACE(source_path, 'C:\\Users\\AORUS\\OneDrive\\tài liệu\\EBOOKS', 'D:\\Extracted-EBOOKS')
    """)
    backs_count = cursor.rowcount
    
    # Update forward slash
    cursor.execute("""
        UPDATE books 
        SET source_path = REPLACE(source_path, 'C:/Users/AORUS/OneDrive/tài liệu/EBOOKS', 'D:/Extracted-EBOOKS')
    """)
    forws_count = cursor.rowcount
    
    conn.commit()
    
    print(f"Update succeeded. Rows changed (Backslashes): {backs_count}, (Forward slashes): {forws_count}")
    
    # In lại để verify
    cursor.execute("SELECT id, title, source_path FROM books LIMIT 5")
    rows = cursor.fetchall()
    
    print("\n=== AFTER UPDATE ===")
    for r in rows:
        print(f"Book {r['id']}: {r['source_path']}")
        
    conn.close()

if __name__ == '__main__':
    main()
