# file-path: epub_inspector.py
# version: 20.3 (AttributeError Hotfix)
# last-updated: 2025-09-26
# description: Fixes the AttributeError by using the correct attribute `item.media_type` instead of the non-existent method `get_media_type()`.

"""
EPUB Structural Inspector v20.3

A diagnostic tool to automatically analyze and report on the structure of an EPUB file.
It performs two main tasks:
1.  Dumps the complete hierarchical Table of Contents (ToC).
2.  Analyzes each unique content document to count heading tags (h1-h6),
    helping to identify potential article separators.
"""

import sys
from pathlib import Path
from collections import Counter
from ebooklib import epub
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# Thay đổi đường dẫn này đến file EPUB bạn muốn phân tích.
EPUB_FILE_PATH = r"D:/Ebooks/Atlas Obscura Wild Life An_ (Z-Library).epub"
OUTPUT_LOG_FILE = "epub_structural_analysis.txt"
# ---------------------

def analyze_toc_structure(toc_items, level=0):
    """Recursively prints the ToC structure to a string."""
    toc_report = ""
    indent = "  " * level
    for item in toc_items:
        if isinstance(item, epub.Link):
            toc_report += f"{indent}- {item.title} (href: {item.href})\n"
        elif isinstance(item, (list, tuple)):
            # Nested section
            section_link, children_items = item[0], item[1]
            toc_report += f"{indent}+ {section_link.title} (href: {section_link.href})\n"
            toc_report += analyze_toc_structure(children_items, level + 1)
    return toc_report

def analyze_html_content(book):
    """Analyzes each content document for heading tag distribution."""
    html_report = ""

    # --- SỬA LỖI TẠI ĐÂY ---
    # Lấy danh sách các item là document một cách chính xác
    content_items = [
        item for item in book.get_items()
        if item.media_type == 'application/xhtml+xml'
    ]

    for item in content_items:
        href = item.get_name()
        html_report += f"--- Analyzing Content File: {href} ---\n"
        try:
            soup = BeautifulSoup(item.get_content(), 'xml')
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if not headings:
                html_report += "  No heading tags found.\n"
            else:
                tag_counts = Counter(tag.name for tag in headings)
                report_line = "  Found: "
                report_line += ", ".join([f"{count}x <{tag}>" for tag, count in tag_counts.items()])
                html_report += report_line + "\n"
        except Exception as e:
            html_report += f"  Could not parse this file. Error: {e}\n"
        html_report += "\n"
    return html_report


def inspect_epub_structure(filepath, output_file):
    """Main function to run the full structural analysis."""
    if not Path(filepath).is_file():
        print(f"Error: File not found at '{filepath}'")
        sys.exit(1)

    try:
        book = epub.read_epub(filepath)
        print(f"Analyzing file: {Path(filepath).name}...")

        # 1. Analyze ToC
        toc_report = analyze_toc_structure(book.toc)

        # 2. Analyze HTML Content Files
        html_report = analyze_html_content(book)

        # 3. Write complete report to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(" EPUB STRUCTURAL ANALYSIS REPORT (v20.3)\n")
            f.write("=" * 80 + "\n")
            f.write(f"File: {Path(filepath).name}\n\n")

            f.write("-" * 30 + "\n")
            f.write(" HIERARCHICAL TABLE OF CONTENTS\n")
            f.write("-" * 30 + "\n")
            f.write(toc_report)
            f.write("\n")

            f.write("=" * 80 + "\n\n")

            f.write("-" * 30 + "\n")
            f.write(" HTML CONTENT ANALYSIS (Heading Tags)\n")
            f.write("-" * 30 + "\n")
            f.write(html_report)

        print(f"Analysis complete. Report saved to '{output_file}'")

    except Exception as e:
        print(f"\n--- An unexpected error occurred ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_epub_structure(EPUB_FILE_PATH, OUTPUT_LOG_FILE)