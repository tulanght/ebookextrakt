import os
import sys
from pathlib import Path
import time
import traceback

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from extract_app.core import epub_parser, pdf_parser

SAMPLES_DIR = Path("test_samples")

def verify_file(filepath: Path):
    print(f"\nEvaluating: {filepath.name}")
    start = time.time()
    try:
        results = {}
        if filepath.suffix.lower() == '.epub':
            results = epub_parser.parse_epub(str(filepath))
        elif filepath.suffix.lower() == '.pdf':
            results = pdf_parser.parse_pdf(str(filepath))
        else:
            print(f"[SKIP] Unsupported format: {filepath.suffix}")
            return
        
        duration = time.time() - start
        
        content = results.get('content', [])
        metadata = results.get('metadata', {})
        
        if not content:
            print(f"[FAIL] No content extracted. Duration: {duration:.2f}s")
            if results.get('error'):
                print(f"       Error: {results.get('error')}")
            else:
                 # Check if it was an empty parse or failed silently
                 pass
        else:
            chapter_count = len(content)
            title = metadata.get('title', 'N/A')
            print(f"[PASS] Extracted {chapter_count} top-level items. Title: '{title}'. Duration: {duration:.2f}s")
            
    except Exception as e:
        print(f"[CRASH] Exception processing file: {e}")
        traceback.print_exc()

def main():
    if not SAMPLES_DIR.exists():
        print(f"Directory not found: {SAMPLES_DIR}")
        return

    files = list(SAMPLES_DIR.glob("*"))
    print(f"Found {len(files)} files in {SAMPLES_DIR}")
    
    for f in files:
        if f.is_file():
            verify_file(f)

if __name__ == "__main__":
    main()
