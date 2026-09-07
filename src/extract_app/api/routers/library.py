# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: library.py
# Version: 1.0.0
# Author: Antigravity
# Description: Library API router for the Electron frontend.
# --------------------------------------------------------------------------------

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from src.extract_app.core.database import DatabaseManager

router = APIRouter(
    prefix="/api/books",
    tags=["Library"]
)

# Initialize database manager
db_manager = DatabaseManager()

@router.get("")
def get_books(q: str = Query(None, description="Search query string")) -> List[Dict[str, Any]]:
    """Retrieve all cataloged books or search books by query."""
    try:
        if q:
            # Need to manually augment total_leaf and translated_count for search results since search_books doesn't join
            # but for now we can just return search results. To keep UI consistent we should use a method that has the counts.
            # But the DatabaseManager's search_books doesn't return counts. We will fetch all and filter if needed, 
            # or rely on the frontend for simple filtering, but let's just return get_all_books and let frontend filter for now.
            # Ideally DatabaseManager would have a joined search.
            books = db_manager.get_all_books()
            search_query = q.lower()
            return [b for b in books if search_query in b.get('title', '').lower() or search_query in b.get('author', '').lower()]
        
        return db_manager.get_all_books()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{book_id}")
def get_book_details(book_id: int) -> Dict[str, Any]:
    """Retrieve full details of a specific book including chapters and articles."""
    try:
        details = db_manager.get_book_details(book_id)
        if not details:
            raise HTTPException(status_code=404, detail="Book not found")
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{book_id}")
def delete_book(book_id: int):
    """Delete a book and all its associated data."""
    try:
        details = db_manager.get_book_details(book_id)
        if not details:
            raise HTTPException(status_code=404, detail="Book not found")
        db_manager.delete_book(book_id)
        return {"status": "success", "message": f"Book {book_id} deleted."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
