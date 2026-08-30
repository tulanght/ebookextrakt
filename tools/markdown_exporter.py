import os
import sys
import re
import yaml
from pathlib import Path
from datetime import date
import unicodedata

# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: tools/markdown_exporter.py
# Version: 1.0.2
# Author: Antigravity
# Description: Script to walk EBOOKS folder and generate content.md with YAML 
#              frontmatter from existing content.txt files.
# --------------------------------------------------------------------------------

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.extract_app.shared.constants import MIN_ARTICLE_BYTES

def slugify(value: str) -> str:
    """Converts string into slug format."""
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)

def cleanup_name(name: str) -> str:
    """Removes leading index numbers e.g. '01 - Bengal Tiger' -> 'Bengal Tiger'"""
    return re.sub(r'^\d+\s*-\s*', '', name).strip()

def map_conservation_status(status_text: str) -> str:
    """Maps full IUCN status to acronym."""
    status_text = status_text.lower()
    mapping = {
        "extinct": "EX",
        "extinct in the wild": "EW",
        "critically endangered": "CR",
        "endangered": "EN",
        "vulnerable": "VU",
        "near threatened": "NT",
        "least concern": "LC",
        "data deficient": "DD",
        "not evaluated": "NE"
    }
    for k, v in mapping.items():
        if k in status_text:
            return v
    return status_text.title()

import json

def load_catalog(json_path: str) -> dict:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
        
EBOOKS_CATALOG = load_catalog(r"C:\Users\AORUS\Documents\Projects\ExtractPDF-EPUB\data\ebooks_catalog.json")

def detect_category(book_title: str) -> str:
    """Ưu tiên folder path (ground truth), fallback về keyword detection."""
    catalog_entry = EBOOKS_CATALOG.get(book_title, {})
    
    folder_path = ""
    if isinstance(catalog_entry, dict):
        folder_path = catalog_entry.get("folder_path", "")
    else:
        folder_path = str(catalog_entry)
        
    path_lower = folder_path.replace('\\', '/').lower()
    
    # Folder-based detection (ground truth)
    if 'prehistoric' in path_lower or 'paleontology' in path_lower:
        return 'Prehistoric'
    if 'birds' in path_lower:
        return 'Aves'
    if 'felid' in path_lower:
        return 'Felidae'
    if 'canid' in path_lower:
        return 'Canidae'
    if 'mammal' in path_lower:
        return 'Mammalia'
    if 'insect' in path_lower or 'bee' in path_lower:
        return 'Insecta'
    if 'fish' in path_lower or 'marine' in path_lower or 'ocean' in path_lower:
        return 'Pisces'
    if 'reptile' in path_lower or 'amphibian' in path_lower or 'snake' in path_lower:
        return 'Reptilia'
    if 'spider' in path_lower or 'arachnid' in path_lower:
        return 'Arachnida'
    if 'botany' in path_lower or 'plant' in path_lower or 'trees' in path_lower:
        return 'Plantae'
    if 'fungi' in path_lower or 'microorganism' in path_lower:
        return 'Fungi'
    if 'ecology' in path_lower or 'conservation' in path_lower or 'wildlife' in path_lower:
        return 'Ecology'
    if 'earth' in path_lower or 'environment' in path_lower:
        return 'Ecology'
    if 'pet' in path_lower or 'domestic' in path_lower:
        return 'Domestic'
    if 'general zoology' in path_lower or 'encyclop' in path_lower:
        return 'Animalia'

    # Fallback: keyword trong book title
    title_lower = book_title.lower()
    if any(k in title_lower for k in ['dinosaur', 'fossil', 'paleonto', 'prehistoric', 'mesozoic', 'jurassic', 'cretaceous']):
        return 'Prehistoric'
    if any(k in title_lower for k in ['bird', 'raptor', 'owl', 'eagle', 'hawk', 'parrot']):
        return 'Aves'
    if any(k in title_lower for k in ['cat', 'lion', 'tiger', 'leopard', 'felid', 'cheetah']):
        return 'Felidae'
    if any(k in title_lower for k in ['wolf', 'dog', 'fox', 'canid', 'coyote']):
        return 'Canidae'
    if any(k in title_lower for k in ['insect', 'ant', 'bee', 'butterfly', 'beetle']):
        return 'Insecta'
    if any(k in title_lower for k in ['shark', 'fish', 'coral', 'ocean', 'marine', 'sea']):
        return 'Pisces'
    if any(k in title_lower for k in ['snake', 'lizard', 'reptile', 'frog', 'amphibian', 'turtle']):
        return 'Reptilia'
    if any(k in title_lower for k in ['succulent', 'cactus', 'cacti', 'plant', 'tree', 'flower', 'botany']):
        return 'Plantae'
    if any(k in title_lower for k in ['ecology', 'ecosystem', 'habitat', 'conservation', 'biodiversity']):
        return 'Ecology'

    # The 6 initial custom fallbacks just to be completely safe for the active files:
    if "cow" in title_lower or "bovidae" in title_lower:
        return "Bovidae"
    if "pig" in title_lower or "suidae" in title_lower:
        return "Suidae"

    return 'Natural History'  # safe default

def extract_folder_index(part: str) -> int:
    """Extracts leading numeric index from folder name, e.g. '03 - Bengal Tiger' -> 3."""
    m = re.match(r'^(\d+)', part)
    return int(m.group(1)) if m else 0

def process_file(txt_file_path: Path, root_dir: Path):
    try:
        if txt_file_path.stat().st_size < MIN_ARTICLE_BYTES:
            return None
    except OSError:
        return None

    with open(txt_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    article_dir = txt_file_path.parent
    rel_path = article_dir.relative_to(root_dir)
    parts = rel_path.parts
    
    if not parts:
        return None
    
    # Hierarchy depth: 1 = book-level, 2 = chapter, 3 = sub-chapter
    hierarchy_depth = len(parts)
    
    # Section index from the leaf folder numeric prefix: "03 - Bengal Tiger" -> 3
    section_index = extract_folder_index(parts[-1]) if len(parts) >= 1 else 0
    # Chapter index from the chapter folder (parts[1] if exists)
    chapter_index = extract_folder_index(parts[1]) if len(parts) >= 2 else 0
        
    book_title_clean = cleanup_name(parts[0])
    
    if len(parts) >= 3:
        chapter_title_clean = cleanup_name(parts[1])
        article_title_clean = cleanup_name(parts[-1])
    elif len(parts) == 2:
        chapter_title_clean = ""
        article_title_clean = cleanup_name(parts[1])
    else:
        chapter_title_clean = ""
        article_title_clean = cleanup_name(parts[0])
    
    # Slugs for ID
    book_slug = slugify(book_title_clean).split('-')[0] # just take first word of book
    chap_slug = slugify(chapter_title_clean).replace('lineage', '').strip('-').split('-')[0] if chapter_title_clean else ""
    art_slug = slugify(article_title_clean)
    
    if chap_slug and chap_slug != "none":
        article_id = f"{book_slug}-ch-{chap_slug}-{art_slug}"
    else:
        article_id = f"{book_slug}-{art_slug}"
    
    # Read images mapping
    images = []
    for ext in ('*.webp', '*.jpg', '*.png', '*.jpeg'):
        for img in article_dir.glob(ext):
            images.append(img.name)
    
    # Content already read above
        
    lines = content.split('\n')
    
    # Parse Species Latin (Line 1 assumed if it's uppercase)
    species_latin = ""
    # Find first non-empty line
    for line in lines:
        if line.strip():
            # If all caps (allowing some spaces), treat as Latin name
            if line.isupper() and len(line) > 3:
                species_latin = line.strip().capitalize()
            break

    # Parse Conservation Status
    conservation_status = ""
    cons_match = re.search(r'CONSERVATION STATUS[^\w]+([^\.]+)', content, re.IGNORECASE)
    if cons_match:
        conservation_status = map_conservation_status(cons_match.group(1))
    
    # Category inference from catalog
    category = detect_category(book_title_clean)
    
    # --- Citation metadata from catalog ---
    # Lookup by matching book_title_clean against catalog keys
    catalog_entry = {}
    for key, entry in EBOOKS_CATALOG.items():
        key_clean = cleanup_name(key)
        if book_title_clean.lower() in key_clean.lower() or key_clean.lower() in book_title_clean.lower():
            catalog_entry = entry
            break
    
    # Parse author from catalog or infer from folder path (parts[0])
    raw_author = catalog_entry.get("author_guess", "") or ""
    # Attempt to extract author from the book folder name: e.g. "Gordon H. Rodda - Lizards..."
    if not raw_author:
        folder_name = parts[0]
        if " - " in folder_name:
            raw_author = folder_name.split(" - ")[0].strip()
    
    pub_year = catalog_entry.get("published_year", "")
    if not pub_year:
        # Try to extract year from folder/key name: e.g. "(2020, Johns Hopkins)"
        year_match = re.search(r'\((\d{4}),', parts[0])
        if year_match:
            pub_year = year_match.group(1)
    
    # Extract publisher from catalog key: e.g. "(2020, Princeton University Press)"
    publisher = ""
    pub_match = re.search(r'\(\d{4},\s*([^)]+)\)', parts[0])
    if pub_match:
        publisher = pub_match.group(1).strip()
    
    source_file = catalog_entry.get("filename", "")
    folder_category = catalog_entry.get("folder_category", "")
        
    # --- Content quality metrics ---
    markdown_body = re.sub(r'\[Image Anchor:[^\]]*\]', '', content)
    word_count = len(markdown_body.split())
    extracted_date = date.today().isoformat()  # e.g. "2026-04-16"
    heading_patterns = [
        "OTHER NAMES", "TAXONOMY", "REPRODUCTION", 
        "BEHAVIOR", "DISTRIBUTION", "HABITAT", 
        "CONSERVATION STATUS", "PHOTO CREDITS"
    ]
    
    for hp in heading_patterns:
        # Adds double newline, ## Heading, and newline if found at the start of a paragraph
        # e.g. "BEHAVIOR Social Behavior: ..." -> "## Behavior\n\nSocial Behavior: ..."
        markdown_body = re.sub(
            fr'^({hp})(:?\s+)', 
            f'## {hp.title()}\n\n', 
            markdown_body, 
            flags=re.MULTILINE
        )
    
    # Create frontmatter
    def safe_str(val):
        stripped = str(val).strip()
        return stripped if stripped and stripped.lower() != "none" else ''

    is_extinct = bool(category == "Prehistoric")
    
    frontmatter = {
        "id": safe_str(article_id),
        # --- Citation fields ---
        "book_title": safe_str(book_title_clean),
        "author": safe_str(raw_author),
        "published_year": safe_str(pub_year),
        "publisher": safe_str(publisher),
        "chapter_title": safe_str(chapter_title_clean),
        "chapter_index": chapter_index,
        "article_title": safe_str(article_title_clean),
        "section_index": section_index,
        "source_file": safe_str(source_file),
        # --- Structure fields ---
        "hierarchy_depth": hierarchy_depth,
        "word_count": word_count,
        "extracted_date": extracted_date,
        # --- Taxonomy / classification fields ---
        "species_latin": safe_str(species_latin),
        "category": safe_str(category),
        "folder_category": safe_str(folder_category),
        "conservation_status": safe_str(conservation_status),
        "is_extinct": is_extinct,
        "time_period": "",
        "ecosystem_type": "",
        "narrative_type": "",
        "images": sorted(images)
    }
    
    # --- Build source attribution block (injected at end of body) ---
    citation_parts = []
    if raw_author:
        citation_parts.append(raw_author)
    if book_title_clean:
        citation_parts.append(f"*{book_title_clean}*")
    if pub_year:
        citation_parts.append(f"({pub_year})")
    if publisher:
        citation_parts.append(publisher)
    if chapter_title_clean:
        citation_parts.append(f"Chương: {chapter_title_clean}")
    attribution_block = "> **Nguồn:** " + ", ".join(citation_parts) if citation_parts else ""
    
    # --- Build final body: H1 heading + body + attribution ---
    h1_title = article_title_clean or book_title_clean
    final_body = f"# {h1_title}\n\n{markdown_body.strip()}"
    if attribution_block:
        final_body += f"\n\n---\n{attribution_block}"
    
    # Build markdown
    md_content = f"---\n{yaml.dump(frontmatter, sort_keys=False, allow_unicode=True)}---\n\n{final_body}"
    
    # Write to content.md
    md_file_path = article_dir / "content.md"
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    return md_file_path

def main():
    import sys
    import argparse
    # Force UTF-8 stdout to avoid Windows cp1252 print errors
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    parser = argparse.ArgumentParser(description='Markdown Exporter')
    parser.add_argument('--dir', type=str, default=r"D:\Extracted-EBOOKS", help='Root directory of EBOOKS')
    args = parser.parse_args()
    
    root_dir = Path(args.dir)
    if not root_dir.exists():
        print(f"Error: Directory '{root_dir}' does not exist.")
        return

    print(f"Scanning EBOOKS root: {root_dir}")
    processed_count = 0
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if 'content.txt' in filenames:
            txt_path = Path(dirpath) / 'content.txt'
            try:
                md_path = process_file(txt_path, root_dir)
                if md_path:
                    processed_count += 1
                # print(f"Exported: {md_path}")
            except Exception as e:
                print(f"Error processing {txt_path}: {e}")
                
    print(f"Extraction complete! Successfully exported {processed_count} Markdown files.")

if __name__ == "__main__":
    main()
