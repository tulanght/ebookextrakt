"""
Ebook Organizer - Scan & classify biology ebooks by filename keywords.

Two scan modes run together:
  1. INBOX: D:/Ebooks/ root - new downloads land here, get sorted into Biology/ or flagged
  2. LIBRARY: D:/Ebooks/Biology/ - reorganize existing biology books by sub-category

Usage:
    python scripts/organize_ebooks.py                  # Dry-run: show report only
    python scripts/organize_ebooks.py --execute        # Actually move files
    python scripts/organize_ebooks.py --review         # Interactive: classify unclassified files
    python scripts/organize_ebooks.py --csv report.csv # Export report to CSV
"""

import os
import re
import sys
import csv
import json
import shutil
from pathlib import Path
from collections import defaultdict

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# -- Configuration -----------------------------------------------------------

INBOX_ROOT = Path("D:/Ebooks")          # New downloads land here
EBOOK_ROOT = Path("D:/Ebooks/Biology")  # Organized biology library
EXTENSIONS = {".pdf", ".epub", ".mobi", ".azw3"}

# Keywords indicating a book IS biology (for inbox triage)
BIOLOGY_KEYWORDS = [
    "animal", "bird", "mammal", "fish", "insect", "reptile", "amphibian",
    "plant", "tree", "fungi", "mushroom", "ecology", "evolution",
    "zoology", "botany", "biology", "species", "wildlife", "nature",
    "natural history", "conservation", "biodiversity", "dinosaur",
    "marine", "ocean", "forest", "spider", "butterfly", "beetle",
    "primate", "whale", "shark", "coral", "fossil", "prehistoric",
    "ornitholog", "entomolog", "herpetolog", "ichthyolog",
    "habitat", "ecosystem", "genus", "taxonom",
]

# Manual overrides file - persists your review decisions
OVERRIDES_FILE = Path(__file__).parent / "ebook_overrides.json"

# Category taxonomy - order matters: first match wins
TAXONOMY = [
    # -- Pets first (before Mammals catches dog/cat) --
    ("Pets and Domestic Animals", [
        "dog breed", "cat breed", "complete dog", "complete cat",
        "dog encyclopedia", "cat encyclopedia",
        " pet ", "pets", "domestic", "aquarium", "terrarium",
        "dog training", "cat care", "veterinar",
    ]),
    # -- Specific animal groups --
    ("Birds", [
        "bird", "birds", "avian", "ornitholog", "parrot", "eagle", "hawk",
        "owl", "penguin", "hummingbird", "songbird", "waterfowl", "raptor",
        "flamingo", "crane", "pigeon", "dove", "sparrow", "finch", "robin",
        "woodpecker", "pelican", "albatross", "swallow", "warbler", "wren",
        "corvid", "crow", "raven", "magpie", "jay", "toucan", "kingfisher",
        "auk", "great auk", "feather", "birding", "birdwatch",
        "chicken", "poultry", "duck", "goose", "swan",
    ]),
    ("Mammals", [
        "mammal", "primate", "monkey", "ape", "gorilla", "chimpanzee",
        "whale", "dolphin", "cetacean", "elephant", "lion", "tiger",
        "bear", "wolf", "wolves", "fox", "deer", "horse", "equine",
        "bat ", " bats", "bat_", "bat-", "bat foraging",
        "carnivore", "carnivoran", "predator",
        "thylacine", "marsupial", "kangaroo", "koala",
        "rhinoceros", "rhino", "hippopotamus", "hippo",
        "cat ", " cats", "big cats", "felid", "panther", "leopard",
        "dog ", " dogs", "canid", "canine",
        "rodent", "mouse", "rat ", " rats",
        "squirrel", "beaver", "otter", "badger", "weasel",
        "giraffe", "zebra", "buffalo", "bison",
        "seal", "sea lion", "walrus", "pinniped",
    ]),
    ("Amphibians and Reptiles", [
        "amphibian", "reptile", "frog", "toad", "salamander", "newt",
        "snake", "lizard", "crocodile", "alligator", "turtle", "tortoise",
        "gecko", "iguana", "chameleon", "python", "cobra", "viper",
        "herpetolog", "herp",
    ]),
    ("Fishes and Marine Life", [
        "fish", "fishes", "shark", "ray ", " rays", "seahorse",
        "coral", "reef", "ocean", "marine", "sea ", " sea",
        "aquatic", "underwater", "deep sea", "deep-sea", "abyss",
        "plankton", "jellyfish", "octopus", "squid", "cephalopod",
        "crustacean", "crab", "lobster", "shrimp",
        "pond", "freshwater", "river life",
    ]),
    ("Insects", [
        "insect", "beetle", "butterfly", "butterflies", "moth",
        "ant ", " ants", "bee ", " bees", "wasp", "hornet",
        "dragonfly", "damselfly", "grasshopper", "cricket",
        "mosquito", "fly ", " flies", "firefly",
        "cicada", "mantis", "cockroach",
        "entomolog", "arthropod",
        "velvet ant",
        "bark beetle", "diving beetle",
        "pollen",
    ]),
    ("Spiders and Arachnids", [
        "spider", "arachnid", "scorpion", "tick", "mite",
    ]),
    ("Botany and Plants", [
        "plant", "flower", "tree", "trees", "botan", "garden",
        "herb", "shrub", "fern", "moss", "lichen",
        "photosynthesis", "seed", "fruit", "leaf", "leaves",
        "rainforest", "forest", "woodland",
        "succulent", "cactus", "orchid", "rose ",
        "rare trees", "botanical",
    ]),
    ("Fungi and Microorganisms", [
        "fungi", "fungus", "mushroom", "mycel", "microb",
        "bacteria", "virus", "microorganism", "micro life",
        "yeast", "mold", "mould",
    ]),
    ("Prehistoric and Paleontology", [
        "prehistoric", "dinosaur", "fossil", "paleontol", "palaeontol",
        "extinct", "ice age", "megafauna", "vanished",
        "jurassic", "cretaceous", "triassic", "cambrian",
        "evolution of",
    ]),
    ("Ecology and Conservation", [
        "ecology", "ecosystem", "conservation", "biodiversity",
        "endangered", "invasive", "habitat", "wildlife recover",
        "climate", "environment", "sustainability",
        "before they vanish", "tenacious beasts",
        "rewild", "at-risk species",
    ]),
    ("General Zoology and Encyclopedias", [
        "zoology", "encyclopedia", "visual guide", "animal atlas",
        "animal book", "DK animal", "smithsonian animal",
        "natural history", "a history of", "100 animals",
        "field guide", "handbook", "compendium",
        "dangerous animal", "dangerous creature", "deadly",
        "animal knowledge", "animal team", "animal fact",
        "creature", "wildlife", "wild life",
        "animals up close", "what's the difference",
        "biology book", "science of animal",
        "30-second",
    ]),
    ("Earth and Environment", [
        "earth", "planet", "antarctica", "desert", "mountain",
        "landscape", "geography", "geological",
        "icy planet", "earth transformed",
    ]),
]

# All category names for validation
CATEGORY_NAMES = [name for name, _ in TAXONOMY] + ["_SKIP", "_NOT_BIOLOGY"]

# Keywords that clearly indicate non-biology content
# IMPORTANT: must be specific enough to avoid false positives on biology books
# (e.g., avoid "history" because "Natural History of..." is common in biology)
NOT_BIOLOGY_KEYWORDS = [
    # IT / Tech (very specific)
    "docker", "kubernetes", "python programming", "javascript", "react.js",
    "machine learning", "deep learning", "neural network",
    "devops", "linux administration", "windows server", "cybersecurity",
    "excel for", "microsoft word", "photoshop",
    # Languages / Learning (very specific phrases)
    "english grammar", "students book", "upper-intermediate", "lower-intermediate",
    "ielts", "toefl", "cambridge english",
    # Business / Finance (very specific)
    "stock market", "personal finance", "accounting for",
    "business management", "startup guide",
    # Human History (specific — NOT "natural history")
    "world war", "world war ii", "roman empire", "medieval history",
    "history of humankind", "history of civilization",
    "sapiens", "homo sapiens history",
    # Cooking / Lifestyle
    "cookbook", " recipes ", "baking guide", "fitness guide", "yoga for",
    # Fiction markers (in parenthetical style common in Z-Library names)
    "(novel)", "(fiction)", "(fantasy novel)", "(thriller)",
]

# Folders to redistribute
FOLDERS_TO_REDISTRIBUTE = {
    "Atlas - Zoology - General",
    "Nature Relate",
}

# Folders to rename (old -> new)
FOLDERS_TO_KEEP = {
    "Birds General Topics": "Birds",
    "Fishes - Oceans": "Fishes and Marine Life",
    "Prehistoric Creatures": "Prehistoric and Paleontology",
    "Trees": "Botany and Plants",
}


# -- Overrides ---------------------------------------------------------------

def load_overrides() -> dict:
    if OVERRIDES_FILE.exists():
        return json.loads(OVERRIDES_FILE.read_text(encoding="utf-8"))
    return {}


def save_overrides(overrides: dict):
    OVERRIDES_FILE.write_text(
        json.dumps(overrides, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# -- Classification Logic ----------------------------------------------------

# Pre-check exclusions to avoid false positives
EXCLUSIONS = {
    "Birds": ["ladybird", "ladybirds", "thunderbird", "firebird", "early bird"],
    "Botany and Plants": ["planet", "transplant", "implant"],
    "Fishes and Marine Life": ["seahorse"],
    "Earth and Environment": ["down to earth", "earth-shattering"],
}


def classify_file(filename: str, overrides: dict = None) -> str:
    """Classify a file based on overrides, then keyword matching."""
    # Check manual overrides first
    if overrides and filename in overrides:
        return overrides[filename]

    name_lower = filename.lower()

    # Check non-biology keywords first
    for kw in NOT_BIOLOGY_KEYWORDS:
        if kw.lower() in name_lower:
            return "_NOT_BIOLOGY"

    for category, keywords in TAXONOMY:
        excluded_kws = EXCLUSIONS.get(category, [])
        skip = False
        for ekw in excluded_kws:
            if ekw in name_lower:
                skip = True
                break
        if skip:
            continue

        for kw in keywords:
            if len(kw) <= 4:
                pattern = (
                    r'(?:^|[\s_\-\(,])'
                    + re.escape(kw.strip())
                    + r'(?:[\s_\-\),.]|$)'
                )
                if re.search(pattern, name_lower):
                    return category
            else:
                if kw.lower() in name_lower:
                    return category

    return "_UNCLASSIFIED"


def is_biology(filename: str) -> bool:
    """Quick check: does this book likely belong in the Biology library?"""
    name_lower = filename.lower()
    return any(kw in name_lower for kw in BIOLOGY_KEYWORDS)


def scan_inbox(inbox: Path, overrides: dict = None) -> list[dict]:
    """Scan D:/Ebooks/ root for new downloads and triage them."""
    results = []
    if not inbox.exists():
        return results

    for f in inbox.iterdir():
        if not (f.is_file() and f.suffix.lower() in EXTENSIONS):
            continue

        category = classify_file(f.name, overrides)

        if category not in ("_UNCLASSIFIED", "_NOT_BIOLOGY"):
            # Clearly biology → classify and move to Biology/
            results.append({
                "file": f,
                "filename": f.name,
                "current_folder": "(inbox)",
                "proposed_category": category,
                "action": "INBOX_TO_BIOLOGY",
            })
        elif is_biology(f.name):
            # Looks like biology but sub-category unknown
            results.append({
                "file": f,
                "filename": f.name,
                "current_folder": "(inbox)",
                "proposed_category": "_UNCLASSIFIED",
                "action": "REVIEW",
            })
        else:
            # Not biology or unclear
            results.append({
                "file": f,
                "filename": f.name,
                "current_folder": "(inbox)",
                "proposed_category": "_NOT_BIOLOGY",
                "action": "REVIEW",
            })

    return results


def scan_ebooks(root: Path, overrides: dict = None) -> list[dict]:
    """Scan all ebook files and classify them."""
    results = []

    # 0. Scan inbox (new downloads in D:/Ebooks/)
    results.extend(scan_inbox(INBOX_ROOT, overrides))

    # 1. Scan loose files at Biology root
    for f in root.iterdir():
        if f.is_file() and f.suffix.lower() in EXTENSIONS:
            category = classify_file(f.name, overrides)
            results.append({
                "file": f,
                "filename": f.name,
                "current_folder": "(root)",
                "proposed_category": category,
                "action": "MOVE" if category != "_UNCLASSIFIED" else "REVIEW",
            })

    # 2. Scan folders to redistribute
    for folder_name in FOLDERS_TO_REDISTRIBUTE:
        folder = root / folder_name
        if not folder.exists():
            continue
        for f in folder.rglob("*"):
            if f.is_file() and f.suffix.lower() in EXTENSIONS:
                category = classify_file(f.name, overrides)
                results.append({
                    "file": f,
                    "filename": f.name,
                    "current_folder": folder_name,
                    "proposed_category": category,
                    "action": "MOVE" if category != "_UNCLASSIFIED" else "REVIEW",
                })

    # 3. Check existing categorized folders for misplaced files
    for old_name, new_name in FOLDERS_TO_KEEP.items():
        folder = root / old_name
        if not folder.exists():
            continue
        for f in folder.rglob("*"):
            if f.is_file() and f.suffix.lower() in EXTENSIONS:
                category = classify_file(f.name, overrides)
                if category == new_name or category == "_UNCLASSIFIED":
                    results.append({
                        "file": f,
                        "filename": f.name,
                        "current_folder": old_name,
                        "proposed_category": new_name,
                        "action": "RENAME_FOLDER",
                    })
                else:
                    results.append({
                        "file": f,
                        "filename": f.name,
                        "current_folder": old_name,
                        "proposed_category": category,
                        "action": "MOVE (misplaced)",
                    })

    # 4. Scan remaining folders for misplaced files
    kept_folders = set(FOLDERS_TO_KEEP.keys()) | FOLDERS_TO_REDISTRIBUTE
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        if folder.name in kept_folders:
            continue
        for f in folder.rglob("*"):
            if f.is_file() and f.suffix.lower() in EXTENSIONS:
                category = classify_file(f.name, overrides)
                if category != "_UNCLASSIFIED" and category != folder.name:
                    results.append({
                        "file": f,
                        "filename": f.name,
                        "current_folder": folder.name,
                        "proposed_category": category,
                        "action": "POSSIBLY_MISPLACED",
                    })

    return results


# -- Report & Execute --------------------------------------------------------

def print_report(results: list[dict]):
    """Print a human-readable report."""
    by_action = defaultdict(list)
    for r in results:
        by_action[r["action"]].append(r)

    print("=" * 80)
    print("EBOOK ORGANIZATION REPORT")
    print(f"Total files to process: {len(results)}")
    print("=" * 80)

    by_category = defaultdict(int)
    for r in results:
        by_category[r["proposed_category"]] += 1

    print("\n[PROPOSED CATEGORY DISTRIBUTION]")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        if cat == "_UNCLASSIFIED":
            marker = " [!] needs manual review"
        elif cat == "_NOT_BIOLOGY":
            marker = " [!] will move to _Review_Not_Biology/"
        else:
            marker = ""
        print(f"  {cat}: {count}{marker}")

    for action in [
        "INBOX_TO_BIOLOGY", "MOVE", "MOVE (misplaced)",
        "RENAME_FOLDER", "POSSIBLY_MISPLACED", "REVIEW",
    ]:
        items = by_action.get(action, [])
        if not items:
            continue
        print(f"\n{'-' * 60}")
        print(f"ACTION: {action} ({len(items)} files)")
        print(f"{'-' * 60}")
        for r in sorted(items, key=lambda x: x["proposed_category"]):
            print(f"  [{r['current_folder']}] -> [{r['proposed_category']}]")
            print(f"    {r['filename']}")


def export_csv(results: list[dict], csv_path: str):
    """Export results to CSV for review."""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["action", "current_folder", "proposed_category", "filename"]
        )
        writer.writeheader()
        for r in sorted(results, key=lambda x: (x["action"], x["proposed_category"])):
            writer.writerow({
                "action": r["action"],
                "current_folder": r["current_folder"],
                "proposed_category": r["proposed_category"],
                "filename": r["filename"],
            })
    print(f"\nExported to: {csv_path}")


def interactive_review(results: list[dict], overrides: dict) -> dict:
    """Interactive CLI to classify unclassified files."""
    unclassified = [r for r in results if r["proposed_category"] == "_UNCLASSIFIED"]

    if not unclassified:
        print("No unclassified files. Nothing to review.")
        return overrides

    # Build numbered category menu
    categories = [name for name, _ in TAXONOMY]
    print("\n" + "=" * 60)
    print(f"INTERACTIVE REVIEW - {len(unclassified)} files to classify")
    print("=" * 60)
    print("\nCategories:")
    for i, cat in enumerate(categories, 1):
        print(f"  {i:2d}. {cat}")
    print(f"   s. Skip (don't move)")
    print(f"   q. Quit review (save progress)")
    print()

    reviewed = 0
    for r in unclassified:
        print(f"[{reviewed + 1}/{len(unclassified)}] {r['filename']}")
        print(f"  Currently in: {r['current_folder']}")

        while True:
            choice = input("  Category number (or s/q): ").strip().lower()

            if choice == "q":
                print(f"\nSaved {reviewed} decisions.")
                save_overrides(overrides)
                return overrides
            elif choice == "s":
                overrides[r["filename"]] = "_SKIP"
                reviewed += 1
                print(f"  -> Skipped")
                break
            elif choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(categories):
                    cat = categories[idx - 1]
                    overrides[r["filename"]] = cat
                    reviewed += 1
                    print(f"  -> {cat}")
                    break
                else:
                    print(f"  Invalid number. Enter 1-{len(categories)}")
            else:
                print(f"  Enter a number (1-{len(categories)}), 's' to skip, 'q' to quit")

    print(f"\nAll {reviewed} files reviewed!")
    save_overrides(overrides)
    return overrides


def execute_moves(results: list[dict], root: Path):
    """Actually move/rename files."""
    moved = 0
    errors = []

    for r in results:
        if r["action"] not in ("MOVE", "MOVE (misplaced)", "INBOX_TO_BIOLOGY"):
            continue
        if r["proposed_category"] in ("_UNCLASSIFIED", "_SKIP"):
            continue

        # Non-biology books go to a review folder, not a permanent category
        if r["proposed_category"] == "_NOT_BIOLOGY":
            target_dir = root / "_Review_Not_Biology"
        else:
            target_dir = root / r["proposed_category"]
        target_dir.mkdir(exist_ok=True)

        src = r["file"]
        dst = target_dir / src.name

        if dst.exists():
            stem = dst.stem
            suffix = dst.suffix
            i = 2
            while dst.exists():
                dst = target_dir / f"{stem} ({i}){suffix}"
                i += 1

        try:
            shutil.move(str(src), str(dst))
            moved += 1
            print(f"  OK {src.name} -> {r['proposed_category']}/")
        except Exception as e:
            errors.append((src, str(e)))
            print(f"  FAIL {src.name}: {e}")

    # Rename kept folders
    for old_name, new_name in FOLDERS_TO_KEEP.items():
        old_path = root / old_name
        new_path = root / new_name
        if old_path.exists() and not new_path.exists():
            try:
                old_path.rename(new_path)
                print(f"  OK Renamed folder: {old_name} -> {new_name}")
            except Exception as e:
                print(f"  FAIL Rename {old_name}: {e}")
        elif old_path.exists() and new_path.exists():
            for f in old_path.rglob("*"):
                if f.is_file():
                    dst = new_path / f.name
                    if not dst.exists():
                        shutil.move(str(f), str(dst))
            try:
                old_path.rmdir()
                print(f"  OK Merged {old_name} into {new_name}")
            except OSError:
                print(f"  WARN {old_name} not empty after merge, check manually")

    # Clean up empty redistributed folders
    for folder_name in FOLDERS_TO_REDISTRIBUTE:
        folder = root / folder_name
        if folder.exists():
            remaining = [
                f for f in folder.rglob("*")
                if f.is_file() and f.name != "desktop.ini"
            ]
            if not remaining:
                shutil.rmtree(str(folder), ignore_errors=True)
                print(f"  OK Removed empty folder: {folder_name}")
            else:
                print(
                    f"  WARN {folder_name} still has"
                    f" {len(remaining)} unclassified files"
                )

    print(f"\nDone: {moved} files moved, {len(errors)} errors")


# -- Main --------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    execute = "--execute" in args
    review = "--review" in args
    csv_path = None

    for i, arg in enumerate(args):
        if arg == "--csv" and i + 1 < len(args):
            csv_path = args[i + 1]

    overrides = load_overrides()
    print(f"Scanning: {EBOOK_ROOT}")
    if overrides:
        print(f"Loaded {len(overrides)} manual overrides from {OVERRIDES_FILE.name}")

    results = scan_ebooks(EBOOK_ROOT, overrides)

    if not results:
        print("No files to process.")
        return

    # Interactive review mode
    if review:
        overrides = interactive_review(results, overrides)
        # Re-scan with updated overrides
        results = scan_ebooks(EBOOK_ROOT, overrides)

    print_report(results)

    if csv_path:
        export_csv(results, csv_path)

    if execute:
        unclassified = [
            r for r in results
            if r["proposed_category"] == "_UNCLASSIFIED"
        ]
        if unclassified:
            print(f"\nWARNING: {len(unclassified)} files still unclassified.")
            ans = input("Continue anyway? (y/n): ").strip().lower()
            if ans != "y":
                print("Aborted.")
                return

        print("\n" + "=" * 60)
        print("EXECUTING MOVES...")
        print("=" * 60)
        execute_moves(results, EBOOK_ROOT)
    elif not review:
        print("\n" + "=" * 60)
        print("DRY RUN - No files were moved.")
        print("  --review   Interactive classify unclassified files")
        print("  --execute  Apply all moves")
        print("  --csv X    Export report to CSV")
        print("=" * 60)


if __name__ == "__main__":
    main()
