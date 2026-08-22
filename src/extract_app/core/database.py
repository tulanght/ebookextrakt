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
    def __init__(self, db_path: str = None):
        if db_path is None:
            from .config import get_user_data_dir
            self.db_path = get_user_data_dir() / "extract.db"
        else:
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

        # 6. API Usage Tracking (Publishing Pipeline)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                stage TEXT,
                engine TEXT,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
            )
        """)

        # 7. Keyword Clusters (Publishing Pipeline)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keyword_clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 8. Cluster Keywords (Publishing Pipeline)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cluster_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_id INTEGER,
                keyword TEXT NOT NULL,
                content_type TEXT,
                is_pillar INTEGER DEFAULT 0,
                word_count_target INTEGER DEFAULT 1500,
                article_id INTEGER DEFAULT NULL,
                publish_status TEXT DEFAULT 'pending',
                keyword_variants TEXT,
                internal_links TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(cluster_id) REFERENCES keyword_clusters(id) ON DELETE CASCADE,
                FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE SET NULL
            )
        """)

        # 9. Compositions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compositions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                focus_keyword TEXT,
                research_notes TEXT,
                composed_text TEXT,
                website_text TEXT,
                facebook_text TEXT,
                word_count INTEGER DEFAULT 0,
                compose_status TEXT DEFAULT 'draft',
                seo_title TEXT,
                meta_description TEXT,
                target_site_id TEXT,
                wp_post_id INTEGER,
                wp_post_url TEXT,
                published_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 10. Composition Sources
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS composition_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                composition_id INTEGER REFERENCES compositions(id) ON DELETE CASCADE,
                article_id INTEGER REFERENCES articles(id) ON DELETE SET NULL,
                order_index INTEGER
            )
        """)

        # Add indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_article_id ON api_usage(article_id)")

        # 11. FTS5 Full-Text Search Index
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                content_text,
                subtitle,
                content='articles',
                content_rowid='id',
                tokenize='porter unicode61'
            )
        """)

        # Trigger: tự động sync khi INSERT article
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS articles_fts_insert
            AFTER INSERT ON articles WHEN new.is_leaf = 1 BEGIN
                INSERT INTO articles_fts(rowid, content_text, subtitle)
                VALUES (new.id, new.content_text, new.subtitle);
            END
        """)

        # Trigger: tự động sync khi UPDATE article
        # Chỉ update index ảo nếu bài viết là leaf
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS articles_fts_update
            AFTER UPDATE ON articles WHEN old.is_leaf = 1 OR new.is_leaf = 1 BEGIN
                INSERT INTO articles_fts(articles_fts, rowid, content_text, subtitle)
                VALUES ('delete', old.id, old.content_text, old.subtitle);
                
                INSERT INTO articles_fts(rowid, content_text, subtitle)
                VALUES (new.id, new.content_text, new.subtitle);
            END
        """)

        # Trigger: tự động sync khi DELETE article
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS articles_fts_delete
            BEFORE DELETE ON articles WHEN old.is_leaf = 1 BEGIN
                INSERT INTO articles_fts(articles_fts, rowid, content_text, subtitle)
                VALUES ('delete', old.id, old.content_text, old.subtitle);
            END
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

        if 'site_category' not in book_cols:
            print("[DB] Migration: Adding site_category to books table.")
            try:
                cursor.execute("ALTER TABLE books ADD COLUMN site_category TEXT DEFAULT NULL")
                conn.commit()
            except Exception as e:
                 print(f"[DB] Book Migration (site_category) failed: {e}")

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

        # Migration v0.4.0: Publishing Pipeline columns
        print("[DB] Migration: Checking publishing pipeline columns in articles.")
        try:
            new_cols = {
                "publish_status": "TEXT DEFAULT 'translated'",
                "wp_post_id": "INTEGER DEFAULT NULL",
                "wp_post_url": "TEXT DEFAULT NULL",
                "published_at": "TIMESTAMP DEFAULT NULL",
                "seo_title": "TEXT DEFAULT NULL",
                "meta_description": "TEXT DEFAULT NULL",
                "focus_keyword": "TEXT DEFAULT NULL",
                "content_brief": "TEXT DEFAULT NULL",
                "brief_generated_at": "TIMESTAMP DEFAULT NULL",
            }
            cols_added = False
            for col, typedef in new_cols.items():
                if col not in art_cols:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col} {typedef}")
                    cols_added = True
            
            if cols_added:
                # Update existing valid translated articles to have base status
                cursor.execute("UPDATE articles SET publish_status = 'translated' WHERE status = 'translated' AND is_leaf = 1")
                conn.commit()
                print("[DB] Publishing columns added.")
        except Exception as e:
             print(f"[DB] Article Migration 5 failed: {e}")

        # Migration: FTS5 index and trigger patch
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles_fts'")
        if not cursor.fetchone():
            print("[DB] Migration: Building FTS5 index (first time, may take a moment)...")
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                    content_text, subtitle,
                    content='articles', content_rowid='id',
                    tokenize='porter unicode61'
                )
            """)
            cursor.execute("""
                INSERT INTO articles_fts(rowid, content_text, subtitle)
                SELECT id, COALESCE(content_text,''), COALESCE(subtitle,'')
                FROM articles
                WHERE is_leaf = 1
            """)
            conn.commit()
            cursor.execute("SELECT COUNT(*) as c FROM articles_fts")
            count = cursor.fetchone()['c']
            print(f"[DB] FTS5 index built: {count:,} articles indexed.")
            
        # Patch v1.1.2: Fix triggers not filtering is_leaf=0
        try:
            # Recreate triggers to ensure they have the WHEN is_leaf=1 condition
            cursor.execute("DROP TRIGGER IF EXISTS articles_fts_insert")
            cursor.execute("DROP TRIGGER IF EXISTS articles_fts_update")
            cursor.execute("DROP TRIGGER IF EXISTS articles_fts_delete")
            
            cursor.execute("""
                CREATE TRIGGER articles_fts_insert
                AFTER INSERT ON articles WHEN new.is_leaf = 1 BEGIN
                    INSERT INTO articles_fts(rowid, content_text, subtitle)
                    VALUES (new.id, new.content_text, new.subtitle);
                END
            """)
            cursor.execute("""
                CREATE TRIGGER articles_fts_update
                AFTER UPDATE ON articles WHEN old.is_leaf = 1 OR new.is_leaf = 1 BEGIN
                    INSERT INTO articles_fts(articles_fts, rowid, content_text, subtitle)
                    VALUES ('delete', old.id, old.content_text, old.subtitle);
                    
                    INSERT INTO articles_fts(rowid, content_text, subtitle)
                    VALUES (new.id, new.content_text, new.subtitle);
                END
            """)
            cursor.execute("""
                CREATE TRIGGER articles_fts_delete
                BEFORE DELETE ON articles WHEN old.is_leaf = 1 BEGIN
                    INSERT INTO articles_fts(articles_fts, rowid, content_text, subtitle)
                    VALUES ('delete', old.id, old.content_text, old.subtitle);
                END
            """)
            conn.commit()
        except Exception as e:
            print(f"[DB] Trigger patch failed: {e}")

        conn.close()

    # --- CRUD Operations ---

    def add_book(self, title: str, author: str, source_path: str, cover_path: str = "", published_year: str = "", category: str = "") -> int:
        """Adds a book to the database. Returns book_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO books (title, author, source_path, cover_path, published_year, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, author, source_path, cover_path, published_year, category))
            
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
                        cover_path: str, structured_content: list, published_year: str = "", category: str = "") -> int:
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
                INSERT OR IGNORE INTO books (title, author, source_path, cover_path, published_year, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (book_title, author, source_path, cover_path, published_year, category))
            
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
                
                # Save the root node and all its children recursively
                # _save_node_batch handles the full tree traversal
                self._save_node_batch(cursor, chapter_id, root_node, 0, None)
            
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
        """Retrieves all books with translation stats (total & translated leaf articles)."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*,
                    COUNT(CASE WHEN a.is_leaf = 1 THEN 1 END) as total_leaf,
                    COUNT(CASE WHEN a.is_leaf = 1 AND a.status = 'translated' THEN 1 END) as translated_count
                FROM books b
                LEFT JOIN chapters c ON c.book_id = b.id
                LEFT JOIN articles a ON a.chapter_id = c.id
                GROUP BY b.id
                ORDER BY b.added_date DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def reset_book_translations(self, book_id: int):
        """Resets the status and translation text of all articles in a book to 'new' and NULL."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE articles 
                SET translation_text = NULL, status = 'new', translated_at = NULL
                WHERE chapter_id IN (SELECT id FROM chapters WHERE book_id = ?)
            """, (book_id,))
            conn.commit()
        finally:
            conn.close()

    def get_dashboard_stats(self) -> Dict[str, int]:
        """Returns total books and total translated articles."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM books")
            books_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM articles WHERE status = 'translated' AND is_leaf = 1")
            articles_count = cursor.fetchone()['count']
            
            return {
                'books': books_count,
                'translated_articles': articles_count
            }
        finally:
            conn.close()

    def get_search_stats(self) -> Dict[str, Any]:
        """Returns total searchable articles and list of distinct site categories."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM articles WHERE is_leaf = 1")
            articles_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT DISTINCT site_category FROM books WHERE site_category IS NOT NULL AND site_category != ''")
            categories = [row['site_category'] for row in cursor.fetchall()]
            
            return {
                'total_articles': articles_count,
                'categories': sorted(categories)
            }
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
                           website_text, facebook_text,
                           publish_status, seo_title, meta_description, focus_keyword, content_brief
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

    def log_api_usage(self, article_id: int, stage: str, engine: str, tokens_in: int, tokens_out: int, duration_seconds: float):
        """Logs API usage info corresponding to an article operation."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO api_usage (article_id, stage, engine, tokens_in, tokens_out, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (article_id, stage, engine, tokens_in, tokens_out, duration_seconds))
            conn.commit()
        finally:
            conn.close()

    def get_article_api_usage(self, article_id: int) -> List[Dict]:
        """Retrieves the API usage records for a given article."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, stage, engine, tokens_in, tokens_out, duration_seconds, created_at 
                FROM api_usage 
                WHERE article_id = ? 
                ORDER BY created_at ASC
            """, (article_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_article_seo(self, article_id: int, seo_title: str, meta_desc: str, keyword: str):
        """Updates SEO metadata for an article."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE articles 
                SET seo_title = ?, meta_description = ?, focus_keyword = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (seo_title, meta_desc, keyword, article_id))
            conn.commit()
        finally:
            conn.close()

    def update_article_brief(self, article_id: int, brief_json: str):
        """Updates the content_brief column for an article."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE articles 
                SET content_brief = ?, brief_generated_at = CURRENT_TIMESTAMP, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (brief_json, article_id))
            conn.commit()
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────
    # Keyword Cluster CRUD (Phase 6)
    # ─────────────────────────────────────────────────────────────────

    def add_keyword_cluster(self, name: str, description: str = "") -> int:
        """Adds a new Keyword Cluster."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO keyword_clusters (name, description)
                VALUES (?, ?)
            """, (name, description))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_keyword_clusters(self) -> List[Dict]:
        """Gets all Keyword Clusters."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM keyword_clusters ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_keyword_cluster(self, cluster_id: int):
        """Deletes a Keyword Cluster and cascades keywords."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("DELETE FROM keyword_clusters WHERE id = ?", (cluster_id,))
            conn.commit()
        finally:
            conn.close()

    def add_cluster_keyword(self, cluster_id: int, keyword: str, content_type: str = "Bài cẩm nang", 
                            is_pillar: bool = False, word_count_target: int = 1500) -> int:
        """Adds a keyword to a cluster."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cluster_keywords (cluster_id, keyword, content_type, is_pillar, word_count_target)
                VALUES (?, ?, ?, ?, ?)
            """, (cluster_id, keyword, content_type, 1 if is_pillar else 0, word_count_target))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_cluster_keywords(self, cluster_id: int) -> List[Dict]:
        """Gets all keywords for a specific cluster."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cluster_keywords WHERE cluster_id = ? ORDER BY is_pillar DESC, created_at ASC", (cluster_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_cluster_keyword_status(self, keyword_id: int, publish_status: str, article_id: int = None):
        """Updates the status and linked article for a cluster keyword."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cluster_keywords 
                SET publish_status = ?, article_id = ?
                WHERE id = ?
            """, (publish_status, article_id, keyword_id))
            conn.commit()
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────
    # FTS5 Search (Phase 7)
    # ─────────────────────────────────────────────────────────────────

    def search_content(
        self,
        query: str,
        site_category: str = None,  # 'animal' | 'plant' | 'overlap' | None (all)
        limit: int = 10,
        min_words: int = 50
    ) -> List[Dict]:
        """
        Full-text search trên toàn bộ articles.content_text.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Safely escape FTS5 query to prevent syntax errors
            safe_words = []
            for word in query.split():
                clean_word = word.replace('"', '').replace("'", "").replace("*", "")
                if clean_word:
                    safe_words.append(f'"{clean_word}"')
            
            if not safe_words:
                return []
                
            fts_query = ' AND '.join(safe_words)
            
            cat_filter = ""
            params = [fts_query]
            if site_category:
                cat_filter = "AND b.site_category = ?"
                params.append(site_category)
            params.append(limit)
            
            cursor.execute(f"""
                SELECT 
                    a.id            AS article_id,
                    b.id            AS book_id,
                    b.title         AS book_title,
                    b.site_category AS site_category,
                    c.title         AS chapter_title,
                    a.subtitle      AS section_title,
                    a.content_text  AS passage,
                    snippet(articles_fts, 0, '<b>', '</b>', '...', 32) AS snippet,
                    articles_fts.rank AS rank,
                    a.word_count
                FROM articles_fts
                JOIN articles a ON a.id = articles_fts.rowid
                JOIN chapters c ON c.id = a.chapter_id
                JOIN books b ON b.id = c.book_id
                WHERE articles_fts MATCH ?
                  AND a.is_leaf = 1
                  AND a.word_count >= {min_words}
                  {cat_filter}
                ORDER BY rank
                LIMIT ?
            """, params)
            
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                words = r['passage'].split()
                if len(words) > 500:
                    r['passage'] = ' '.join(words[:500]) + '...'
                results.append(r)
            
            return results
        finally:
            conn.close()

    def rebuild_fts_index(self) -> int:
        """
        Rebuild toàn bộ FTS5 index từ đầu.
        Returns: số articles đã index.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO articles_fts(articles_fts) VALUES('rebuild')")
            conn.commit()
            cursor.execute("SELECT COUNT(*) as c FROM articles_fts")
            return cursor.fetchone()['c']
        finally:
            conn.close()

    def fts_search_raw(
        self,
        fts_query: str,
        site_category: str = None,
        limit: int = 100,
        min_words: int = 80,
        exclude_article_ids: List[int] = None,
        book_category: str = None
    ) -> List[Dict]:
        """
        Raw FTS5 search with optional article exclusion.
        book_category: lọc theo cột books.category (genre/scope, vd 'concept') —
            khác site_category (domain animal/plant). Dùng cho bài khái niệm chỉ tra
            sách sinh thái đại cương, tránh nhiễu chuyên khảo loài.
        Returns: article_id, book_id, book_title, site_category,
                 chapter_title, section_title, passage, rank, word_count
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            params = [fts_query]

            where_extra = ""
            if site_category:
                where_extra += " AND b.site_category = ?"
                params.append(site_category)

            if book_category:
                where_extra += " AND b.category = ?"
                params.append(book_category)

            if exclude_article_ids:
                placeholders = ','.join('?' * len(exclude_article_ids))
                where_extra += f" AND a.id NOT IN ({placeholders})"
                params.extend(exclude_article_ids)

            params.append(limit)

            cursor.execute(f"""
                SELECT
                    a.id AS article_id,
                    b.id AS book_id,
                    b.title AS book_title,
                    b.site_category AS site_category,
                    c.title AS chapter_title,
                    a.subtitle AS section_title,
                    a.content_text AS passage,
                    articles_fts.rank AS rank,
                    a.word_count
                FROM articles_fts
                JOIN articles a ON a.id = articles_fts.rowid
                JOIN chapters c ON c.id = a.chapter_id
                JOIN books b ON b.id = c.book_id
                WHERE articles_fts MATCH ?
                  AND a.is_leaf = 1
                  AND a.word_count >= {min_words}
                  AND a.word_count <= 3000
                  AND LOWER(COALESCE(a.subtitle, '')) NOT LIKE '%literature cited%'
                  AND LOWER(COALESCE(a.subtitle, '')) NOT LIKE '%references%'
                  AND LOWER(COALESCE(a.subtitle, '')) NOT LIKE '%bibliography%'
                  AND LOWER(COALESCE(a.subtitle, '')) NOT LIKE '%glossary%'
                  AND LOWER(COALESCE(a.subtitle, '')) NOT LIKE '%appendix%'
                  AND LOWER(COALESCE(a.subtitle, '')) NOT LIKE '% index'
                  AND LOWER(COALESCE(a.subtitle, '')) NOT LIKE 'index %'
                  {where_extra}
                ORDER BY rank
                LIMIT ?
            """, params)

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

        # Generate bash script
    def qmd_search(
        self,
        query: str,
        site_category: str = None,
        collection: str = 'ebooks-all',
        limit: int = 100,
        min_words: int = 80,
        exclude_article_ids: List[int] = None
    ) -> List[Dict]:
        """
        QMD hybrid search (BM25+vector+rerank). Same return shape as fts_search_raw().
        Requires: qmd CLI installed (bun link), index built, JINA_API_KEY set.
        """
        import subprocess
        import os
        env = os.environ.copy()
        env['QMD_EMBED_PROVIDER'] = 'jina'
        env['JINA_API_KEY'] = 'jina_ed71ffbdfe574f1db4bde55234c89d2f8JUlgQYMwmb6n7SdAucVibHQrQO3'
        env['QMD_JINA_MODEL'] = 'jina-embeddings-v5-text-small'
        env['QMD_JINA_DIMENSION'] = '1024'

        cwd = r"C:\Users\AORUS\Documents\Projects\_research\qmd"
        bun_exe = r"C:\Users\AORUS\.bun\bin\bun.exe"

        # Vector search aligns better with English corpus when query is English-only.
        # Strip Vietnamese/diacritic terms — keep ASCII words (English + scientific names).
        import re as _re
        _ascii_terms = [w for w in query.split() if w.isascii() and len(w) > 2]
        vsearch_query = ' '.join(_ascii_terms) if _ascii_terms else query
        print(f"     [vsearch] query: '{vsearch_query}'")

        cmd = [bun_exe, 'run', 'qmd', 'vsearch', vsearch_query, '--json', '-n', str(limit * 2), '--no-rerank']
        if collection:
            cmd += ['-c', collection]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', shell=True, env=env, cwd=cwd)

        if result.returncode != 0:
            print(f"[QMD Error] {result.stderr}")
            return []

        try:
            qmd_results = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"[QMD Error] Failed to parse output: {result.stdout[:200]}")
            return []

        if not qmd_results:
            return []

        import re

        def slugify(text: str) -> str:
            return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')

        def extract_folder_slug(qmd_file: str) -> str:
            norm = qmd_file.replace('\\', '/')
            if 'qmd://' in norm:
                try:
                    after = norm.split('://')[1]  # collection/folder/...
                    return after.split('/', 1)[1].split('/')[0]
                except IndexError:
                    return ''
            parts = norm.split('/Extracted-EBOOKS/')
            if len(parts) > 1:
                return slugify(parts[1].split('/')[0])
            return ''

        # Load all books from DB to match QMD folder slugs → book metadata + passages
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            query_sql = """
                SELECT
                    a.id AS article_id,
                    b.id AS book_id,
                    b.title AS book_title,
                    b.site_category AS site_category,
                    c.title AS chapter_title,
                    a.subtitle AS section_title,
                    a.content_text AS passage,
                    a.word_count
                FROM articles a
                JOIN chapters c ON c.id = a.chapter_id
                JOIN books b ON b.id = c.book_id
                WHERE a.is_leaf = 1
                  AND a.word_count >= {min_words}
                  AND a.word_count <= 5000
            """.format(min_words=min_words)
            params = []
            if site_category:
                query_sql += " AND b.site_category = ?"
                params.append(site_category)
            if exclude_article_ids:
                ex_ph = ','.join('?' * len(exclude_article_ids))
                query_sql += f" AND a.id NOT IN ({ex_ph})"
                params.extend(exclude_article_ids)
            cursor.execute(query_sql, params)
            db_articles = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

        # Index DB articles by book_title_slug for fast lookup
        db_by_book_slug: dict = {}
        for art in db_articles:
            bslug = slugify(art['book_title'])
            db_by_book_slug.setdefault(bslug, []).append(art)

        # Find which book_ids are relevant (via QMD folder slug matching)
        relevant_book_ids: set = set()
        qmd_book_score: dict = {}  # book_id → best QMD score
        for qres in qmd_results:
            score = qres.get('score', 0.0)
            if score < 0.25:  # lowered from 0.3 — mixed-language queries score slightly lower
                continue
            folder_slug = extract_folder_slug(qres.get('file', ''))
            candidates = db_by_book_slug.get(folder_slug, [])
            for art in candidates:
                bid = art['book_id']
                relevant_book_ids.add(bid)
                if score > qmd_book_score.get(bid, 0):
                    qmd_book_score[bid] = score

        if not relevant_book_ids:
            return []

        # Use FTS5 to find keyword-relevant passages within the QMD-identified books.
        # Ebooks are in English — use ASCII-only words. AND for core terms, OR for extras.
        clean = re.sub(r'[^\w\s]', ' ', query)
        ascii_words = [w for w in clean.split() if w.isascii() and len(w) > 2]
        if len(ascii_words) >= 2:
            # Core 2-term AND constraint (must co-occur in passage) + OR for remaining terms
            core = f'"{ascii_words[0]}" AND "{ascii_words[1]}"'
            extras = [f'"{w}"' for w in ascii_words[2:]]
            fts_query = f'({core})' + (' OR ' + ' OR '.join(extras) if extras else '')
        else:
            fts_query = ' OR '.join(f'"{w}"' for w in ascii_words) if ascii_words else '"the"'

        conn2 = self._get_connection()
        try:
            cur2 = conn2.cursor()
            book_ph = ','.join('?' * len(relevant_book_ids))
            params2: list = []
            ex_clause = ''
            if exclude_article_ids:
                ex_ph = ','.join('?' * len(exclude_article_ids))
                ex_clause = f" AND a.id NOT IN ({ex_ph})"
                params2.extend(exclude_article_ids)

            fts_sql = f"""
                SELECT
                    a.id AS article_id,
                    b.id AS book_id,
                    b.title AS book_title,
                    b.site_category AS site_category,
                    c.title AS chapter_title,
                    a.subtitle AS section_title,
                    a.content_text AS passage,
                    a.word_count,
                    rank AS fts_rank
                FROM articles_fts
                JOIN articles a ON articles_fts.rowid = a.id
                JOIN chapters c ON c.id = a.chapter_id
                JOIN books b ON b.id = c.book_id
                WHERE articles_fts MATCH ?
                  AND b.id IN ({book_ph})
                  AND a.is_leaf = 1
                  AND a.word_count >= {min_words}
                  AND a.word_count <= 5000
                  {ex_clause}
                ORDER BY rank
                LIMIT {limit * 3}
            """
            all_params = [fts_query] + list(relevant_book_ids) + params2
            try:
                cur2.execute(fts_sql, all_params)
                fts_articles = [dict(row) for row in cur2.fetchall()]
            except Exception:
                # FTS syntax error fallback — return all articles from relevant books sorted by word_count desc
                fts_articles = [
                    art for art in db_articles
                    if art['book_id'] in relevant_book_ids
                ]
                fts_articles.sort(key=lambda a: -a['word_count'])
        finally:
            conn2.close()

        # Deduplicate by article_id, inject book QMD score as rank
        seen_article_ids: set = set()
        final_results = []
        for art in fts_articles:
            aid = art['article_id']
            if aid in seen_article_ids:
                continue
            if exclude_article_ids and aid in exclude_article_ids:
                continue
            seen_article_ids.add(aid)
            mapped = art.copy()
            mapped['rank'] = -(qmd_book_score.get(art['book_id'], 0) * 20.0)
            mapped['_query_matched'] = query
            final_results.append(mapped)
            if len(final_results) >= limit:
                break

        return final_results