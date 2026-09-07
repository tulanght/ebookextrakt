import argparse
import json
import sys
import re

# Force UTF-8 for Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.extract_app.core.database import DatabaseManager

def _count_concrete_markers(text: str) -> int:
    """Đếm số liệu, tên khoa học, đơn vị đo — markers của fact cụ thể."""
    count = 0
    count += len(re.findall(r'\b\d+(?:\.\d+)?\b', text))           # numbers
    count += len(re.findall(r'\b[A-Z][a-z]+ [a-z]+\b', text))      # scientific names
    count += len(re.findall(r'\b\d+\s*(?:kg|g|m|cm|ft|in|lb|oz|mph|kph|km|mi)\b', text, re.I))  # units
    count += len(re.findall(r'\b(?:19|20)\d{2}\b', text))          # years
    return count

def _extract_snippet(text: str, query: str = "", max_words: int = 150) -> str:
    """Extract ~max_words window centered on first keyword match in text."""
    text = re.sub(r'^#+\s+.+$', '', text, flags=re.MULTILINE).strip()
    text = re.sub(r'\n{2,}', '\n\n', text)
    words = text.split()
    if len(words) <= max_words:
        return text

    # Extract plain keywords from FTS5 syntax (strip NEAR, AND/OR, quotes, parens)
    plain = re.sub(r'NEAR\(([^,)]+).*?\)', r'\1', query)
    plain = re.sub(r'["\(\),]', ' ', plain)
    plain = re.sub(r'\b(AND|OR|NOT)\b', ' ', plain, flags=re.I)
    keywords = [w.strip().lower() for w in plain.split() if len(w.strip()) > 2]

    # Find earliest keyword position in text (char offset)
    text_lower = text.lower()
    best_char = None
    for kw in keywords:
        idx = text_lower.find(kw)
        if idx != -1 and (best_char is None or idx < best_char):
            best_char = idx

    if best_char is None:
        # No keyword found — fall back to beginning
        snippet_words = words[:max_words + 30]
        snippet = ' '.join(snippet_words)
        cut = snippet.rfind('. ', len(' '.join(words[:max_words - 20])))
        return (snippet[:cut + 1] if cut != -1 else ' '.join(words[:max_words]) + '...')

    # Convert char offset to word index
    cumlen = 0
    kw_word_idx = 0
    for i, w in enumerate(words):
        if cumlen >= best_char:
            kw_word_idx = i
            break
        cumlen += len(w) + 1

    # Center window around keyword word index
    half = max_words // 2
    start = max(0, kw_word_idx - half)
    end = min(len(words), start + max_words + 30)
    start = max(0, end - max_words - 30)

    snippet = ' '.join(words[start:end])

    # Trim leading partial sentence if not at doc start
    if start > 0:
        cut_start = snippet.find('. ')
        if cut_start != -1 and cut_start < 80:
            snippet = snippet[cut_start + 2:]

    # Trim to sentence boundary at end
    target_len = len(' '.join(words[start:start + max_words]))
    cut_end = snippet.rfind('. ', 0, target_len + 50)
    if cut_end != -1:
        snippet = snippet[:cut_end + 1]
    elif len(snippet.split()) > max_words:
        snippet = ' '.join(snippet.split()[:max_words]) + '...'

    return snippet

def _score_passage(passage: dict, section: dict, used_book_ids_in_section: set) -> float:
    """Lower = better (giống FTS5 rank convention)."""
    base = passage['rank']

    # Bonus concreteness (nếu section.require_concrete = True)
    if section.get('require_concrete'):
        concrete = _count_concrete_markers(passage['passage'])
        base -= concrete * 0.3

    # Penalty nặng nếu là trang Index hoặc Glossary
    title = str(passage.get('section_title', '')).lower()
    chap = str(passage.get('chapter_title', '')).lower()
    if 'index' in title or 'index' in chap or 'glossary' in title:
        base += 100.0
        
    # Penalty nặng nếu passage quá dài (thường là list / index)
    if passage.get('word_count', 0) > 1500:
        base += 50.0

    # Penalty nếu cuốn đã được dùng trong section này
    if passage['book_id'] in used_book_ids_in_section:
        base += 5.0

    return base

def run_research(plan_path: Path, force: bool = False, dry_run: bool = False, backend: str = 'fts5'):
    if not plan_path.exists():
        print(f"Error: Plan file not found: {plan_path}")
        sys.exit(1)

    with open(plan_path, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    slug = plan.get('slug', 'unknown')
    output_dir = plan_path.parent

    print(f"[*] Starting research for '{slug}' (Backend: {backend})")
    
    if not dry_run:
        db = DatabaseManager()
    
    global_used_ids = set()
    summary_data = []
    total_sources_used = set()
    total_passages = 0
    total_words = 0

    for section in plan.get('sections', []):
        sid = section['id']
        title = section['title']
        queries = section.get('queries', [])
        cat = section.get('category', plan.get('default_category'))
        if cat is not None:
            cat_str = str(cat).strip().lower()
            if cat_str.isdigit():
                # Map WordPress category IDs to database site_category
                # 231 (Động vật hoang dã), 235 (Thú), etc. -> 'animal'
                cat = 'animal'
            elif cat_str not in ('animal', 'plant', 'overlap', 'unclassified', 'off'):
                cat = None
        target_passages = section.get('target_passages', 3)
        require_concrete = section.get('require_concrete', False)
        # corpus = scope sách theo books.category (vd 'concept' → chỉ sách sinh thái đại cương).
        # Khác 'category' (= site_category domain). Section không có corpus → tra toàn corpus.
        book_corpus = section.get('corpus')
        
        print(f"  -> Processing section: [{sid}] {title}")
        
        if dry_run:
            print(f"     (Dry Run) Queries to run: {queries}")
            continue
            
        pool = {}
        for query in queries:
            if backend == 'qmd':
                # Collection naming convention: ebooks-{cat}
                collection = 'ebooks-all'
                results = db.qmd_search(
                    query=query,
                    site_category=cat,
                    collection=collection,
                    limit=15,
                    min_words=80,
                    exclude_article_ids=list(global_used_ids)
                )
            else:
                results = db.fts_search_raw(
                    fts_query=query,
                    site_category=cat,
                    limit=15,
                    min_words=80,
                    exclude_article_ids=list(global_used_ids),
                    book_category=book_corpus
                )
            for res in results:
                # Deduplicate by article_id in the pool, keep lowest rank
                aid = res['article_id']
                if aid not in pool or res['rank'] < pool[aid]['rank']:
                    res['_query_matched'] = query
                    pool[aid] = res
                    
        # Ranking pool
        pool_list = list(pool.values())
        used_book_ids_in_section = set()
        
        # We need to sort by score. But score depends on used_book_ids_in_section.
        # So we pick one by one greedily.
        selected_passages = []
        while pool_list and len(selected_passages) < target_passages:
            # Score all remaining in pool based on CURRENT used_book_ids_in_section
            for p in pool_list:
                p['_score'] = _score_passage(p, section, used_book_ids_in_section)
                
            # Sort ascending
            pool_list.sort(key=lambda x: x['_score'])
            
            best = pool_list.pop(0)
            
            # Enforce max 1 passage per book in a section if possible?
            # Penalty is +5.0 which heavily discourages it, but doesn't strictly prevent it if no other books exist.
            # The spec says: "Pick top N passages, max 1 passage/book trong section"
            # So let's strictly enforce unless absolutely necessary...
            # The spec literally says "max 1 passage/book trong section".
            if best['book_id'] in used_book_ids_in_section:
                continue # strictly max 1 per book!
                
            # OK, we take it
            selected_passages.append(best)
            used_book_ids_in_section.add(best['book_id'])
            global_used_ids.add(best['article_id'])
            total_sources_used.add(best['book_id'])

        # Write section Markdown
        out_md_path = output_dir / f"{sid}.md"
        if out_md_path.exists() and not force:
            print(f"     [!] Warning: {sid}.md already exists. Skipping (use --force to overwrite).")
        else:
            words_in_section = 0
            with open(out_md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Section: {title}\n")
                f.write(f"Section ID: {sid} | Passages: {len(selected_passages)} sources\n\n")
                f.write("## Queries used\n")
                for q in queries:
                    f.write(f"- `{q}`\n")
                f.write("\n---\n\n")
                
                for idx, p in enumerate(selected_passages, 1):
                    source_title = p['book_title']
                    book_cat = p['site_category']
                    chap = p['chapter_title']
                    sub = p['section_title']
                    rank = p['rank']
                    wc = p['word_count']
                    
                    text = _extract_snippet(p['passage'], p.get('_query_matched', ''))
                    text = re.sub(r'!\[[^\]]*\]\([^)]*\)\s*', '', text)
                    words_in_section += len(text.split())
                    
                    f.write(f"### [{idx}] {source_title} · {book_cat}\n")
                    f.write(f"> {chap} › {sub} | {wc} words in source | rank {rank:.2f}\n\n")
                    f.write(f"{text}\n\n---\n\n")
            
            total_passages += len(selected_passages)
            total_words += words_in_section

            # Track for summary
            status = "✅ OK"
            if len(selected_passages) == 0:
                status = "❌ Gap"
            elif len(selected_passages) < target_passages:
                status = "⚠ Short"
                
            summary_data.append({
                'id': sid,
                'title': title,
                'target': target_passages,
                'found': len(selected_passages),
                'books': len(used_book_ids_in_section),
                'status': status
            })

    if not dry_run:
        # Generate _summary.md
        summary_path = output_dir / "_summary.md"
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"# Research Summary: {plan.get('topic')}\n")
            f.write(f"Slug: {slug} | Article type: {plan.get('article_type')} | Date: {date_str} | Backend: {backend}\n\n")
            
            f.write("## Sections\n")
            f.write("| ID | Title | Target | Found | Books | Status |\n")
            f.write("|----|-------|--------|-------|-------|--------|\n")
            for s in summary_data:
                f.write(f"| {s['id']} | {s['title']} | {s['target']} | {s['found']} | {s['books']} | {s['status']} |\n")
            
            f.write("\n## Total stats\n")
            f.write(f"- Sources: {len(total_sources_used)} unique books\n")
            f.write(f"- Total passages: {total_passages}\n")
            f.write(f"- Total research words: ~{total_words}\n")
            f.write(f"- Estimated token usage: ~{int(total_words * 1.3)}\n")
            
        print(f"[*] Done! Wrote summary to _summary.md")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Research Pipeline v2")
    parser.add_argument('--plan', type=str, required=True, help="Path to _plan.json")
    parser.add_argument('--force', action='store_true', help="Overwrite existing markdown files")
    parser.add_argument('--dry-run', action='store_true', help="Check plan without searching")
    parser.add_argument('--backend', type=str, choices=['fts5', 'qmd'], default='fts5', help="Search backend to use (default: fts5)")
    
    args = parser.parse_args()
    run_research(Path(args.plan).resolve(), force=args.force, dry_run=args.dry_run, backend=args.backend)

