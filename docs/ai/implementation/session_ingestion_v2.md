# Session Memory: Ebook Ingestion V2 Pipeline & Smart Deduplication

**Date**: 2026-08-22
**Focus**: Refactoring Ebook Management, Dynamic Dashboard, and Duplicate Handling.

## Architectural Changes
1. **Dynamic Path Resolution**: 
   - Shifted away from hard-coded `PREDEFINED_CATEGORIES`. 
   - The UI (Library View & Ingestion View) now dynamically resolves categories by scanning subdirectories within the physical root `D:\Ebooks\Biology`, `_Review_Not_Biology`, and `_UNCLASSIFIED`.
2. **Hybrid Classification Pipeline**:
   - Step 1: AI (Vertex AI) cleans the text sample to extract safe titles and authors.
   - Step 2: Rule Engine (`scripts.organize_ebooks.classify_file`) routes the file to the correct destination directory based on keyword matching.
3. **Smart Cleanup & send2trash Integration**:
   - Replaced basic deduplication logic that left remnant files in the `Downloads` directory.
   - Integrated `send2trash` to safely move duplicates and bad files straight to the OS Recycle Bin.
   - Added a "Batch Delete" UI action for one-click cleanup.
   - Modified the background `_ai_worker` thread with a full `try-except-finally` wrapper to prevent UI freezes on thread crash.
   - Auto-deletes files (Late Duplicate Detection) if the AI identifies them as existing in the database after renaming.

## Key Files Touched
- `src/extract_app/modules/ui/ingestion_view.py`: Heavy rewrite for UI dynamic categories, `send2trash` integration, thread-safety, and batch operations.
- `src/extract_app/core/database.py` & `storage_handler.py`: Added `category` column to track physical classification mappings.
- `CHANGELOG.md`: Updated with version 2.3.0.

## Future Recommendations
- If `send2trash` needs to be rolled back or adjusted for other OSes, use platform-specific checks.
- Continue migrating other hardcoded UI components to dynamic, data-driven structures.
