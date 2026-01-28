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
        # Added translation_text and status in v1.1
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id INTEGER,
                subtitle TEXT,
                content_text TEXT,
                translation_text TEXT,
                status TEXT DEFAULT 'new',
                order_index INTEGER,
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

        conn.commit()
        conn.close()
        
        self._check_migrations()

    def _check_migrations(self):
        """Checks and applies necessary migrations (e.g. adding columns)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check articles table for 'status' column
        cursor.execute("PRAGMA table_info(articles)")
        columns = [row['name'] for row in cursor.fetchall()]
        
        if 'status' not in columns:
            print("[DB] Applying migration: Adding status and translation_text to articles.")
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN status TEXT DEFAULT 'new'")
                cursor.execute("ALTER TABLE articles ADD COLUMN translation_text TEXT")
                conn.commit()
            except Exception as e:
                print(f"[DB] Migration failed: {e}")
        
        conn.close()

    # --- CRUD Operations ---

    def add_book(self, title: str, author: str, source_path: str, cover_path: str = "") -> int:
        """Adds a book to the database. Returns book_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO books (title, author, source_path, cover_path)
                VALUES (?, ?, ?, ?)
            """, (title, author, source_path, cover_path))
            
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

    def add_article(self, chapter_id: int, subtitle: str, content: str, order_index: int) -> int:
        """Adds an article to a chapter."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO articles (chapter_id, subtitle, content_text, order_index)
                VALUES (?, ?, ?, ?)
            """, (chapter_id, subtitle, content, order_index))
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

    def update_article_translation(self, article_id: int, translation_text: str, status: str):
        """Updates translation text and status for an article."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE articles 
                SET translation_text = ?, status = ?
                WHERE id = ?
            """, (translation_text, status, article_id))
            conn.commit()
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
                    SELECT id, subtitle, status, translation_text, order_index 
                    FROM articles 
                    WHERE chapter_id = ? 
                    ORDER BY order_index
                """, (chapter['id'],))
                chapter['articles'] = [dict(row) for row in cursor.fetchall()]
                result['chapters'].append(chapter)
                
            return result
        finally:
            conn.close()
