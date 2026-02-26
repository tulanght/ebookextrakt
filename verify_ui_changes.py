
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
    
    print("Importing StorageHandler...")
    from extract_app.core import storage_handler
    
    print("Importing LibraryView...")
    from extract_app.modules.ui import library_view
    
    print("Importing EditorView...")
    from extract_app.modules.ui import editor_view
    
    print("✅ All imports successful.")
    
    # Optional: Mock instantiation if possible given Tcl/Tk dependency (might fail without display)
    # So we just trust imports for syntax checking.
    
except Exception as e:
    print(f"❌ Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
