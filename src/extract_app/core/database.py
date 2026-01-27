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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id INTEGER,
                subtitle TEXT,
                content_text TEXT, 
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
            
    def get_all_books(self) -> List[Dict]:
        """Retrieves all books."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books ORDER BY added_date DESC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
