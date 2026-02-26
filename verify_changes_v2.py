
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

try:
    print("Importing DatabaseManager...")
    from extract_app.core.database import DatabaseManager
    
    print("Importing WebviewGenerator...")
    from extract_app.core import webview_generator
    
    print("Importing LibraryView...")
    from extract_app.modules.ui import library_view
    
    print("Checking DatabaseManager methods...")
    db = DatabaseManager()
    if not hasattr(db, 'get_article_images'):
        raise Exception("DatabaseManager missing get_article_images")
        
    print("Checking EditorView methods...")
    from extract_app.modules.ui.editor_view import DualViewEditor
    if not hasattr(DualViewEditor, '_preview_webview'):
        raise Exception("DualViewEditor missing _preview_webview")

    print("Checking TranslationService protection...")
    from extract_app.core.translation_service import TranslationService
    if not hasattr(TranslationService, '_protect_anchors'):
        raise Exception("TranslationService missing _protect_anchors")

    print("Checking Webview Generator regex...")
    with open("src/extract_app/core/webview_generator.py", "r", encoding="utf-8") as f:
        content = f.read()
        if "safe = safe.replace(/^(#{1,6})" not in content:
             # Just a loose check for the regex string or part of it
             if "Markdown Headings" not in content:
                 raise Exception("Webview Generator missing Markdown Heading logic")
        
    print("✅ All imports and method checks successful.")
    
except Exception as e:
    print(f"❌ Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
