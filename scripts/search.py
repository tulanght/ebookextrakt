#!/usr/bin/env python3
"""
FTS5 Search CLI
Allows searching through extracted books via the FTS5 index.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import argparse
import json
from pathlib import Path

# Setup paths so we can import src
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from extract_app.core.database import DatabaseManager

def main():
    parser = argparse.ArgumentParser(description="Search extracted ebooks using FTS5.")
    parser.add_argument("query", nargs="?", type=str, help="Search query string")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results (default 10)")
    parser.add_argument("--category", type=str, choices=["animal", "plant", "overlap", "off"],
                        help="Filter by site_category: animal, plant, overlap, off")
    parser.add_argument("--format", type=str, choices=["json", "markdown"], default="json",
                        help="Output format (default json)")
    parser.add_argument("--min-words", type=int, default=50, help="Minimum words in a result passage (default 50)")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the FTS5 index from scratch")
    
    args = parser.parse_args()
    
    db = DatabaseManager()
    
    if args.rebuild:
        print("Rebuilding FTS5 index... This may take a while depending on DB size.")
        count = db.rebuild_fts_index()
        print(f"FTS5 rebuild complete. {count:,} articles indexed.")
        sys.exit(0)
        
    if not args.query:
        # If not rebuilding, a query is required
        print("Error: A search query is required.")
        parser.print_help()
        sys.exit(1)
        
    # Check if FTS index has data
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM articles_fts")
    fts_count = cursor.fetchone()['c']
    conn.close()
    
    if fts_count == 0:
        print("FTS5 index is empty. Rebuilding automatically...")
        db.rebuild_fts_index()

    # Perform the search
    results = db.search_content(
        query=args.query,
        site_category=args.category,
        limit=args.limit,
        min_words=args.min_words
    )
    
    if not results:
        print(f"No results found for '{args.query}'", file=sys.stderr)
        if args.category:
            print(f"Note: Filtered by category='{args.category}'", file=sys.stderr)
        sys.exit(0)
        
    if args.format == "json":
        output = {
            "query": args.query,
            "total_results": len(results),
            "results": []
        }
        for item in results:
            output["results"].append({
                "rank": round(item["rank"], 4),
                "book": item["book_title"],
                "chapter": item["chapter_title"],
                "section": item["section_title"],
                "word_count": item["word_count"],
                "snippet": item["snippet"],
                "passage": item["passage"],
                "site_category": item["site_category"]
            })
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    elif args.format == "markdown":
        print(f"## Search: \"{args.query}\" — {len(results)} results\n")
        
        for i, item in enumerate(results, 1):
            book = item['book_title']
            ch = item['chapter_title']
            sec = item['section_title']
            cat = item['site_category']
            words = item['word_count']
            
            section_display = f" › {sec}" if sec and sec != ch else ""
            title_line = f"### [{i}] {book} › {ch}{section_display}"
            
            print(title_line)
            print(f"*{words} words | category: {cat}*")
            print()
            print(f"> {item['snippet']}")
            print()
            print(item['passage'])
            print("\n---\n")

if __name__ == "__main__":
    main()
