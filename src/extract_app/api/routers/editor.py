# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: editor.py
# Version: 1.0.0
# Author: Antigravity
# Description: Editor API router for fetching and updating article content.
# --------------------------------------------------------------------------------

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from src.extract_app.core.database import DatabaseManager

router = APIRouter(
    prefix="/api/editor",
    tags=["Editor"]
)

db_manager = DatabaseManager()

class TranslationUpdate(BaseModel):
    translation_text: str
    status: str
    note: str = "User Save"

@router.get("/articles/{article_id}")
def get_article(article_id: int) -> Dict[str, Any]:
    """Retrieve article content and metadata for editing."""
    try:
        # We need more than just content_text, we need translation_text, status, subtitle.
        # But `db_manager.get_article_content()` only returns `content_text`.
        # Let's query it directly or rely on the book details.
        # Since book details returns articles array with `translation_text`, it might be easier
        # to just use a custom query here for performance, or fetch via book.
        # I'll use a direct cursor query to get full details of an article.
        
        conn = db_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, chapter_id, subtitle, content_text, translation_text, status, word_count FROM articles WHERE id = ?", (article_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Article not found")
            
        return dict(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/articles/{article_id}")
def update_article(article_id: int, payload: TranslationUpdate) -> Dict[str, Any]:
    """Update article translation and status."""
    try:
        db_manager.update_article_translation(
            article_id=article_id, 
            translation_text=payload.translation_text, 
            status=payload.status, 
            note=payload.note
        )
        return {"status": "success", "message": "Article saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
