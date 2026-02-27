# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/database.py
# Version: 1.0.0
# Author: Antigravity
# Description: Manages SQLite database interactions effectively for the application.
# --------------------------------------------------------------------------------

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class DatabaseManager:
    """
    Handles SQLite database connections and strict schema management.
    """
    
    def __init__(self, db_path: str = "user_data/extract.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    def _init_db(self):
        """Initializes the database schema if not exists."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Books Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                cover_path TEXT,
                source_path TEXT UNIQUE,
                category TEXT,
                tags TEXT,
                published_year TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Chapters Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                title TEXT,
                order_index INTEGER,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            )
        """)

        # 3. Articles Table (Leaf nodes of content)
        # Added translation_text and status in v1.1, is_leaf in v1.2
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id INTEGER,
                subtitle TEXT,
                content_text TEXT,
                translation_text TEXT,
                status TEXT DEFAULT 'new',
                is_leaf INTEGER DEFAULT 1,
                order_index INTEGER,
                word_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP,
                translated_at TIMESTAMP,
                FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
            )
        """)
        
        # 4. Images Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                path TEXT,
                caption TEXT,
                FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
            )
        """)

        # 5. Translation Revisions Table (WordPress-style)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translation_revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                content_text TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()
        
        self._check_migrations()



    def _check_migrations(self):
        """Checks and applies necessary migrations (e.g. adding columns)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # --- Books Table Migrations ---
        cursor.execute("PRAGMA table_info(books)")
        book_cols = [row['name'] for row in cursor.fetchall()]
        
        if 'category' not in book_cols:
             print("[DB] Migration: Adding category/tags to books file.")
             try:
                 cursor.execute("ALTER TABLE books ADD COLUMN category TEXT")
                 cursor.execute("ALTER TABLE books ADD COLUMN tags TEXT")
                 conn.commit()
             except Exception as e:
                 print(f"[DB] Book Migration failed: {e}")

        if 'published_year' not in book_cols:
             print("[DB] Migration: Adding published_year to books table.")
             try:
                 cursor.execute("ALTER TABLE books ADD COLUMN published_year TEXT")
                 conn.commit()
             except Exception as e:
                 print(f"[DB] Book Migration (published_year) failed: {e}")

        # --- Articles Table Migrations ---
        cursor.execute("PRAGMA table_info(articles)")
        art_cols = [row['name'] for row in cursor.fetchall()]
        
        # Existing migrations
        if 'status' not in art_cols:
            print("[DB] Migration: Adding status/translation_text to articles.")
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN status TEXT DEFAULT 'new'")
                cursor.execute("ALTER TABLE articles ADD COLUMN translation_text TEXT")
                conn.commit()
            except Exception as e:
                 print(f"[DB] Article Migration 1 failed: {e}")
                 
        if 'is_leaf' not in art_cols:
            print("[DB] Migration: Adding is_leaf to articles.")
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN is_leaf INTEGER DEFAULT 1")
                conn.commit()
            except Exception as e:
                 print(f"[DB] Article Migration 2 failed: {e}")

        # New migrations (v0.2.0)
        if 'word_count' not in art_cols:
            print("[DB] Migration: Adding word_count/timestamps to articles.")
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN word_count INTEGER DEFAULT 0")
                cursor.execute("ALTER TABLE articles ADD COLUMN last_updated TIMESTAMP")
                cursor.execute("ALTER TABLE articles ADD COLUMN translated_at TIMESTAMP")
                
                # Update existing word counts
                print("[DB] Calculating word counts for existing articles...")
                cursor.execute("SELECT id, content_text FROM articles")
                rows = cursor.fetchall()
                for row in rows:
                    wc = len(row['content_text'].split()) if row['content_text'] else 0
                    cursor.execute("UPDATE articles SET word_count = ? WHERE id = ?", (wc, row['id']))
                
                conn.commit()
                print("[DB] Optimization complete.")
            except Exception as e:
                 print(f"[DB] Article Migration 3 failed: {e}")
        
        # Migration v0.3.0: Article variants (website/facebook text)
        if 'website_text' not in art_cols:
            print("[DB] Migration: Adding website_text/facebook_text to articles.")
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN website_text TEXT")
                cursor.execute("ALTER TABLE articles ADD COLUMN facebook_text TEXT")
                conn.commit()
                print("[DB] Variant columns added.")
            except Exception as e:
                 print(f"[DB] Article Migration 4 failed: {e}")

        conn.close()

    # --- CRUD Operations ---

    def add_book(self, title: str, author: str, source_path: str, cover_path: str = "", published_year: str = "") -> int:
        """Adds a book to the database. Returns book_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO books (title, author, source_path, cover_path, published_year)
                VALUES (?, ?, ?, ?, ?)
            """, (title, author, source_path, cover_path, published_year))
            
            # If ignore happened (duplicate), we need the ID
            if cursor.lastrowid and cursor.lastrowid > 0:
                book_id = cursor.lastrowid
            else:
                cursor.execute("SELECT id FROM books WHERE source_path = ?", (source_path,))
                result = cursor.fetchone()
                book_id = result['id'] if result else -1
            
            conn.commit()
            return book_id
        finally:
            conn.close()

    def add_chapter(self, book_id: int, title: str, order_index: int) -> int:
        """Adds a chapter to a book."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chapters (book_id, title, order_index)
                VALUES (?, ?, ?)
            """, (book_id, title, order_index))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def add_article(self, chapter_id: int, subtitle: str, content: str, order_index: int, is_leaf: bool = True) -> int:
        """Adds an article to a chapter. is_leaf=True means this is actual content, False means it's a container."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            word_count = len(content.split()) if content else 0
            cursor.execute("""
                INSERT INTO articles (chapter_id, subtitle, content_text, order_index, is_leaf, word_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (chapter_id, subtitle, content, order_index, 1 if is_leaf else 0, word_count))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def add_image(self, article_id: int, path: str, caption: str):
        """Adds an image ref to an article."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO images (article_id, path, caption)
                VALUES (?, ?, ?)
            """, (article_id, path, caption))
            conn.commit()
        finally:
            conn.close()

    def get_article_images(self, article_id: int) -> List[Dict]:
        """Retrieves images for an article."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT path, caption FROM images WHERE article_id = ?", (article_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_article_translation(self, article_id: int, translation_text: str, status: str, note: str = "User Save"):
        """Updates translation text and status for an article, and saves a revision."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # 1. Update main article
            cursor.execute("""
                UPDATE articles 
                SET translation_text = ?, status = ?, translated_at = CURRENT_TIMESTAMP, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (translation_text, status, article_id))
            
            # 2. Save revision
            self._add_translation_revision(cursor, article_id, translation_text, note)
            
            conn.commit()
        finally:
            conn.close()

    def _add_translation_revision(self, cursor, article_id: int, content_text: str, note: str):
        """Helper to add a revision record."""
        cursor.execute("""
            INSERT INTO translation_revisions (article_id, content_text, note)
            VALUES (?, ?, ?)
        """, (article_id, content_text, note))

    def get_translation_revisions(self, article_id: int) -> List[Dict]:
        """Retrieves revision history for an article."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, content_text, note, created_at 
                FROM translation_revisions 
                WHERE article_id = ? 
                ORDER BY created_at DESC
            """, (article_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_article_content(self, article_id: int) -> str:
        """Retrieves content text for a specific article."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT content_text FROM articles WHERE id = ?", (article_id,))
            result = cursor.fetchone()
            return result['content_text'] if result else ""
        finally:
            conn.close()
    
    def save_book_batch(self, book_title: str, author: str, source_path: str, 
                        cover_path: str, structured_content: list, published_year: str = "") -> int:
        """
        Saves all book data (chapters, articles, images) in a SINGLE transaction.
        This is MUCH faster than individual insert calls.
        
        structured_content is a tree: [{ title, content, children: [...] }, ...]
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. Insert Book
            cursor.execute("""
                INSERT OR IGNORE INTO books (title, author, source_path, cover_path, published_year)
                VALUES (?, ?, ?, ?, ?)
            """, (book_title, author, source_path, cover_path, published_year))
            
            if cursor.lastrowid and cursor.lastrowid > 0:
                book_id = cursor.lastrowid
            else:
                cursor.execute("SELECT id FROM books WHERE source_path = ?", (source_path,))
                result = cursor.fetchone()
                book_id = result['id'] if result else -1
            
            if book_id == -1:
                conn.rollback()
                return -1
            
            # 2. Process each top-level node as a Chapter
            for chap_idx, root_node in enumerate(structured_content):
                chap_title = root_node.get('title', f"Chapter {chap_idx+1}")
                cursor.execute("""
                    INSERT INTO chapters (book_id, title, order_index)
                    VALUES (?, ?, ?)
                """, (book_id, chap_title, chap_idx))
                chapter_id = cursor.lastrowid
                
                # Save root node if it has content
                if root_node.get('content'):
                    self._save_node_batch(cursor, chapter_id, root_node, 0, None)
                
                # Save children
                for art_idx, child in enumerate(root_node.get('children', [])):
                    self._save_node_batch(cursor, chapter_id, child, art_idx + 1, None)
            
            # 3. Commit everything at once
            conn.commit()
            return book_id
            
        except Exception as e:
            conn.rollback()
            print(f"[DB] Batch save error: {e}")
            return -1
        finally:
            conn.close()
    
    def _save_node_batch(self, cursor, chapter_id: int, node: dict, order_index: int, parent_id: int):
        """
        Recursively saves a node and its children using an existing cursor.
        Does NOT commit - caller handles transaction.
        """
        from pathlib import Path
        
        subtitle = node.get('title', 'Untitled')
        content_list = node.get('content', [])
        children = node.get('children', [])
        is_leaf = len(children) == 0
        
        # Build text content
        full_text = []
        images_to_save = []
        
        for content_type, data in content_list:
            if content_type == 'text':
                if isinstance(data, dict):
                    full_text.append(data.get('content', ''))
                else:
                    full_text.append(str(data))
            elif content_type == 'image' and isinstance(data, dict):
                anchor = data.get('anchor', '')
                if anchor:
                    full_text.append(f"[Image: {Path(anchor).name}]")
                    images_to_save.append({
                        'path': anchor,
                        'caption': data.get('caption', '')
                    })
        
        text_content = "\n\n".join(full_text)
        
        word_count = len(text_content.split()) if text_content else 0
        
        # Insert article
        cursor.execute("""
            INSERT INTO articles (chapter_id, subtitle, content_text, order_index, is_leaf, word_count, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (chapter_id, subtitle, text_content, order_index, 1 if is_leaf else 0, word_count))
        article_id = cursor.lastrowid
        
        # Insert images
        for img in images_to_save:
            cursor.execute("""
                INSERT INTO images (article_id, path, caption)
                VALUES (?, ?, ?)
            """, (article_id, img['path'], img['caption']))
        
        # Recurse for children
        for i, child_node in enumerate(children):
            self._save_node_batch(cursor, chapter_id, child_node, order_index + 1000 + i, article_id)
            
    def get_all_books(self) -> List[Dict]:
        """Retrieves all books."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books ORDER BY added_date DESC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def search_books(self, query: str) -> List[Dict]:
        """Search books by title or author."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            search_query = f"%{query}%"
            cursor.execute("""
                SELECT * FROM books 
                WHERE title LIKE ? OR author LIKE ?
                ORDER BY added_date DESC
            """, (search_query, search_query))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_book(self, book_id: int):
        """Deletes a book (and cascades to chapters/articles)."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Enable FK support just in case, though usually on by default in new sqlite3 lib
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
        finally:
            conn.close()

    def get_book_details(self, book_id: int) -> Dict[str, Any]:
        """
        Retrieves full book details: Metadata, Chapters, and Articles (lite info).
        Used for the detail view.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. Book Info
            cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            if not book:
                return {}
            
            result = dict(book)
            result['chapters'] = []
            
            # 2. Chapters
            cursor.execute("SELECT * FROM chapters WHERE book_id = ? ORDER BY order_index", (book_id,))
            chapters = [dict(row) for row in cursor.fetchall()]
            
            # 3. Articles (for each chapter)
            # Fetch all articles for this book efficiently via JOIN?
            # Or just loop. Loop is fine for typical book size (~20-50 chapters).
            for chapter in chapters:
                cursor.execute("""
                    SELECT id, subtitle, status, translation_text, is_leaf, order_index, 
                           word_count, last_updated, translated_at,
                           website_text, facebook_text
                    FROM articles 
                    WHERE chapter_id = ? 
                    ORDER BY order_index
                """, (chapter['id'],))
                chapter['articles'] = [dict(row) for row in cursor.fetchall()]
                result['chapters'].append(chapter)
                
            return result
        finally:
            conn.close()

    def update_article_variant(self, article_id: int, variant_type: str, text: str):
        """Updates a variant column (website_text or facebook_text) for an article."""
        allowed = {'website': 'website_text', 'facebook': 'facebook_text'}
        col = allowed.get(variant_type)
        if not col:
            raise ValueError(f"Invalid variant type: {variant_type}")
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE articles SET {col} = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?", (text, article_id))
            conn.commit()
        finally:
            conn.close()
