
import sys
import os
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

from extract_app.core.pdf_parser import parse_pdf
from extract_app.core.epub_parser import parse_epub

SAMPLES_DIR = "test_samples"

def main():
    if not os.path.exists(SAMPLES_DIR):
        print(f"Error: Directory '{SAMPLES_DIR}' not found.")
        return

    files = [f for f in os.listdir(SAMPLES_DIR) if f.lower().endswith(('.pdf', '.epub'))]
    
    if not files:
        print(f"No PDF/EPUB files found in '{SAMPLES_DIR}'.")
        return

    print(f"Found {len(files)} files. Starting baseline check...\n")
    print("-" * 60)

    results = []

    for filename in files:
        filepath = os.path.join(SAMPLES_DIR, filename)
        file_ext = os.path.splitext(filename)[1].lower()
        print(f"Processing: {filename}...")
        
        status = "UNKNOWN"
        details = ""

        try:
            if file_ext == '.pdf':
                res = parse_pdf(filepath)
            elif file_ext == '.epub':
                res = parse_epub(filepath)
            else:
                res = None
            
            # Basic validation of result structure
            if res and isinstance(res, dict) and 'content' in res:
                content = res['content']
                if content: # Assuming non-empty content means success
                    status = "SUCCESS"
                    chapter_count = len(content)
                    details = f"Extracted {chapter_count} chapters."
                else:
                    # Check if it returned an error structure
                    if len(content) == 1 and content[0].get('title') == 'Error':
                         status = "FAILURE"
                         details = content[0]['content'][0][1] # Extract error message
                    else:
                        status = "WARNING"
                        details = "Result returned but content list is empty."
            else:
                status = "FAILURE"
                details = "Invalid result format returned."

        except Exception as e:
            status = "CRASH"
            details = str(e)
            # traceback.print_exc() # Uncomment for deep debug

        print(f"  -> [{status}] {details}")
        results.append({'file': filename, 'status': status, 'details': details})
        print("-" * 60)

    print("\nSUMMARY REPORT:")
    print("=" * 60)
    for item in results:
        status_icon = "✅" if item['status'] == "SUCCESS" else "❌"
        if item['status'] == "WARNING": status_icon = "⚠️"
        print(f"{status_icon} {item['file']}: {item['status']}")
        if item['status'] != "SUCCESS":
             print(f"   Reason: {item['details']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
