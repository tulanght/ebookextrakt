# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: ingest.py
# Version: 1.0.0
# Author: Antigravity
# Description: Ingestion API router for processing PDF and EPUB uploads.
# --------------------------------------------------------------------------------

import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from src.extract_app.core.database import DatabaseManager
from src.extract_app.core.config import get_user_data_dir
from src.extract_app.core.pdf_parser import parse_pdf
from src.extract_app.core.epub_parser import parse_epub

router = APIRouter(
    prefix="/api/ingest",
    tags=["Ingestion"]
)

db_manager = DatabaseManager()

@router.post("/upload")
async def upload_and_process(file: UploadFile = File(...)):
    """Uploads a file, extracts its content, and saves it to the database."""
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if ext not in ['pdf', 'epub']:
        raise HTTPException(status_code=400, detail="Only PDF and EPUB files are supported.")
        
    try:
        # Save uploaded file temporarily to library directory
        lib_dir = get_user_data_dir() / "library"
        lib_dir.mkdir(parents=True, exist_ok=True)
        
        safe_title = "".join(c for c in file.filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        dest_path = lib_dir / safe_title
        
        # Prevent collisions
        counter = 1
        while dest_path.exists():
            dest_path = lib_dir / f"{dest_path.stem}_{counter}.{ext}"
            counter += 1
            
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Parse based on extension
        results = {}
        if ext == 'pdf':
            results = parse_pdf(str(dest_path))
        elif ext == 'epub':
            results = parse_epub(str(dest_path))
            
        # Extract metadata
        meta = results.get('metadata', {})
        book_title = meta.get('title') or dest_path.stem
        author = meta.get('author', 'Unknown Author')
        published_year = str(meta.get('year', ''))
        cover_path = meta.get('cover_image_path', '')
        
        # Save to database
        book_id = db_manager.save_book_batch(
            book_title=book_title,
            author=author,
            source_path=str(dest_path),
            cover_path=cover_path,
            published_year=published_year,
            structured_content=results.get('content', [])
        )
        
        if book_id == -1:
             raise Exception("Failed to save book to database")
             
        return {
            "status": "success",
            "message": f"Successfully ingested {file.filename}",
            "book_id": book_id,
            "title": book_title
        }
        
    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()
