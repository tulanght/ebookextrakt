# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: scripts/batch_processor.py
# Description: Batch processes files in test_samples to verify stability.
# --------------------------------------------------------------------------------

import sys
import os
import glob
from pathlib import Path

# Force UTF-8 for batch processing output
sys.stdout.reconfigure(encoding='utf-8')

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from extract_app.core import epub_parser, pdf_parser

def process_file(filepath):
    print(f"Processing: {filepath}")
    ext = Path(filepath).suffix.lower()
    try:
        if ext == '.pdf':
            res = pdf_parser.parse_pdf(filepath)
        elif ext == '.epub':
            res = epub_parser.parse_epub(filepath)
        else:
            print("  [SKIP] Unsupported format")
            return

        error = res.get('error')
        if error:
            print(f"  [FAIL] Error: {error}")
        else:
            content = res.get('content', [])
            print(f"  [PASS] Extracted {len(content)} top-level items.")
            # Deep check for smart splitting
            total_articles = 0
            for item in content:
                # content can be list of articles or raw content list (if simple structure)
                # Structure: item = {'title':..., 'content': [...], 'children': [...]}
                # item['content'] is list of articles (dicts) if structured, or raw tuples?
                # Dependent on parser.
                # PDF: structure_pdf_articles returns list of Dict.
                
                # Check directly
                c_list = item.get('content', [])
                if isinstance(c_list, list) and c_list and isinstance(c_list[0], dict) and 'subtitle' in c_list[0]:
                     total_articles += len(c_list)
                else:
                     # Maybe raw content or just 1 article
                     total_articles += 1
                     
            print(f"         Total sub-articles estimated: {total_articles}")

    except Exception as e:
        print(f"  [CRASH] Exception: {e}")

def main():
    test_dir = Path("test_samples")
    if not test_dir.exists():
        print(f"Directory not found: {test_dir}")
        return

    files = list(test_dir.glob("**/*.pdf")) + list(test_dir.glob("**/*.epub"))
    
    print(f"Found {len(files)} files to test.")
    for f in files:
        process_file(str(f))

if __name__ == "__main__":
    main()
