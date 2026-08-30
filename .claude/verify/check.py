#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bo do bat bien cho dot nap kho Thuc vat (8 viec P0).

Chay DOC LAP - khong doc bao cao cua script thi cong.
  python .claude/verify/check.py           # day du (quet ca dia, ~30s)
  python .claude/verify/check.py --fast    # bo qua quet dia

Exit 0 = dat het. Exit 1 = co bat bien bi pha -> DUNG, khoi phuc backup.
"""
import sqlite3, sys, re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "user_data" / "extract.db"
GARDEN = Path(r"D:\Garden Home and Plants")
FAST = "--fast" in sys.argv

BASE = {"articles": 95628, "books": 1264, "txt_files": 38283,
        "anchors_db_start": 886, "plant_books": 63, "plant_leaf": 11188, "dup_titles": 121}

rows, failed = [], 0


def chk(ok, name, got, want, note="", hard=True):
    """hard=True: bat bien, pha la DUNG. hard=False: muc tieu cua dot nay."""
    global failed
    tag = ("PASS" if ok else ("FAIL" if hard else "TODO"))
    rows.append((tag, name, str(got), str(want), note))
    if not ok and hard:
        failed += 1


def q(conn, sql):
    return conn.execute(sql).fetchone()[0]


conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

# --- Nhom 1: khong duoc mat du lieu ------------------------------------
a = q(conn, "SELECT COUNT(*) FROM articles")
b = q(conn, "SELECT COUNT(*) FROM books")
chk(a >= BASE["articles"], "1. articles khong giam", a, f">={BASE['articles']}",
    "GIAM = co DELETE. Don != Xoa!")
chk(b >= BASE["books"], "2. books khong giam", b, f">={BASE['books']}", "")

# --- Nhom 2: master tren dia phai nguyen ven ---------------------------
if FAST:
    rows.append(("SKIP", "3. so file content.txt", "-", BASE["txt_files"], "--fast"))
    rows.append(("SKIP", "4. anchor CON trong content.txt", "-", ">0", "--fast"))
    rows.append(("SKIP", "5. anchor HET trong content.md", "-", "0", "--fast"))
elif not GARDEN.exists():
    rows.append(("SKIP", "3-5. kiem tra dia", "-", "-", "khong thay kho vuon"))
else:
    txts = list(GARDEN.rglob("content.txt"))
    mds = list(GARDEN.rglob("content.md"))
    chk(len(txts) == BASE["txt_files"], "3. so file content.txt", len(txts),
        BASE["txt_files"], "lech = da dung vao master")
    n_anchor_txt = sum(1 for p in txts[:3000]
                       if "[Image Anchor:" in p.read_text("utf-8", errors="ignore"))
    chk(n_anchor_txt > 0, "4. anchor CON trong content.txt", f"{n_anchor_txt}/3000",
        ">0", "=0 la MAT du lieu dich sach!")
    n_anchor_md = sum(1 for p in mds[:3000]
                      if "[Image Anchor:" in p.read_text("utf-8", errors="ignore"))
    chk(n_anchor_md == 0, "5. anchor HET trong content.md", f"{n_anchor_md}/{min(len(mds),3000)}",
        "0", "exporter chua strip" if n_anchor_md else "")

# --- Nhom 3: muc tieu cua dot nay --------------------------------------
anc = q(conn, "SELECT COUNT(*) FROM articles WHERE content_text LIKE '%[Image Anchor:%'")
chk(anc == 0, "6. anchor HET trong DB", anc, 0,
    f"khoi diem {BASE['anchors_db_start']}", hard=False)

dup = conn.execute("""
    SELECT COUNT(*) FROM (
      SELECT LOWER(REPLACE(REPLACE(REPLACE(title,' ',''),'-',''),'''','')) k
      FROM books GROUP BY k HAVING COUNT(*) > 1)
""").fetchone()[0]
chk(dup <= BASE["dup_titles"], "7. trung title KHONG tang", dup,
    f"<={BASE['dup_titles']}", "tang = dedup hong -> ban ghi doi")

fts = q(conn, "SELECT COUNT(*) FROM articles_fts")
leaf = q(conn, "SELECT COUNT(*) FROM articles WHERE is_leaf=1")
chk(fts == leaf, "8. articles_fts == leaf", f"{fts} vs {leaf}", "bang nhau",
    "lech = index chua container is_leaf=0", hard=False)

# --- Nhom 4: hop dong voi 3 consumer ------------------------------------
src = (ROOT / "src" / "extract_app" / "core" / "database.py").read_text("utf-8", errors="ignore")
m = re.search(r"def fts_search_raw\((.*?)\)\s*->", src, re.S)
need = ["fts_query", "site_category", "limit", "min_words", "exclude_article_ids", "book_category"]
miss = [p for p in need if not m or p not in m.group(1)]
chk(not miss, "9. fts_search_raw() nguyen chu ky", "thieu:" + ",".join(miss) if miss else "du",
    "du 6 tham so", "VO HOP DONG CPC + KDV_Reel" if miss else "")

rp = (ROOT / "scripts" / "research.py").read_text("utf-8", errors="ignore")
fmiss = [f for f in ["--plan", "--backend", "--force"] if f not in rp]
chk(not fmiss, "10. research.py giu CLI", "thieu:" + ",".join(fmiss) if fmiss else "du",
    "--plan/--backend/--force", "VO HOP DONG CPC" if fmiss else "")

# --- Tien do (khong phai bat bien) --------------------------------------
pb = q(conn, "SELECT COUNT(*) FROM books WHERE site_category='plant'")
pl = q(conn, """SELECT COUNT(*) FROM articles a JOIN chapters c ON c.id=a.chapter_id
                JOIN books b ON b.id=c.book_id WHERE b.site_category='plant' AND a.is_leaf=1""")
nul = q(conn, "SELECT COUNT(*) FROM books WHERE site_category IS NULL")
conn.close()

w = [max(len(str(r[i])) for r in rows) for i in range(5)]
print("\n=== BAT BIEN ===")
for r in rows:
    print(f"  [{r[0]:4}] {r[1]:<{w[1]}}  {r[2]:>{w[2]}} / {r[3]:<{w[3]}}  {r[4]}")
print(f"\n=== TIEN DO (tham khao) ===")
print(f"  plant books : {pb:>6}   (khoi diem {BASE['plant_books']}, dich ~297)")
print(f"  plant leaf  : {pl:>6}   (khoi diem {BASE['plant_leaf']}, dich ~36000)")
print(f"  site_cat NULL:{nul:>6}   (khoi diem 861, dich 0 neu gop backfill)")
print(f"\n{'*** CO ' + str(failed) + ' BAT BIEN BI PHA -> DUNG, KHOI PHUC BACKUP ***' if failed else '=== BAT BIEN OK (TODO = muc tieu chua dat, binh thuong truoc khi thi cong) ==='}")
sys.exit(1 if failed else 0)
