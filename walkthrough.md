# Implementation Check — Python Ingestion Stability

Date: 2026-09-06
Branch: `feature/ingest-pipeline-v2`

## Scope and reference documents

- `docs/ai/implementation/session_ingestion_v2.md`
- `docs/ai/testing/feature-python-baseline-stability.md`
- `ROADMAP.md` — Python stability before Electron

The implementation correctly moves the ingestion root to `INBOX_ROOT`, delegates
classification to `AIClassifier` plus the filename rule engine, and prevents a failed
Recycle Bin call from falling back to permanent `Path.unlink()` deletion.

## Verification evidence

```text
tests/: 132 passed, 5 warnings in 8.72s
manual: AI normalization completed and the confirmed duplicate appeared in Recycle Bin
```

Unscoped repository-root `pytest` is not green because it collects four standalone
manual/integration scripts outside `tests/` that require obsolete credentials, a
removed module, or a live external embedding model.

## Blocking findings

1. Duplicate lookup does not exclude the source path. Reclassifying a library file
   whose normalized name is unchanged can identify the file itself as a duplicate and
   send it to Recycle Bin (`ingestion_view.py:354-365`, `734-760`).
2. `_remove_and_quarantine` deletes the database row and commits before calling
   `send2trash`. A Recycle Bin failure therefore leaves the physical ebook in place
   but irreversibly removes its catalog row (`ingestion_view.py:421-432`).
3. `send2trash` is imported by production code but is absent from `requirements.txt`.
   A clean environment created from the manifest cannot reliably start the app.

## Important findings

1. When a registered source file is discarded as a physical duplicate, its `db_info`
   row is not reconciled; the database may retain a path to the recycled file.
2. `_clean_single_worker` runs in a background queue but calls `_quarantine_file`,
   which writes to Tk widgets directly through `_insert_log` instead of scheduling via
   `_safe_log`.
3. scan and batch paths accept MOBI/AZW3, while the dashboard still lists only
   PDF/EPUB files (`ingestion_view.py:171`).
4. Two cleanup workers perform a non-atomic check-then-move sequence, so concurrent
   copies can both pass duplicate detection.
5. The diff contains trailing whitespace, an unused `db_titles` set, and a redundant
   first loop over `dynamic_cats`.
6. Automated tests do not cover self-match exclusion, DB/Recycle Bin transaction
   ordering, background UI dispatch, concurrent duplicate processing, or MOBI/AZW3
   dashboard visibility.

## Decision

Original review status: **not ready to merge**. The blocking findings below were
subsequently converted into RED tests and resolved in the GREEN follow-up.

## TDD RED follow-up — 2026-09-07

Five behavior-level regression tests now reproduce all three blocking findings:

```text
tests/test_ingestion_safety.py: 4 passed, 5 failed
tests/: 132 passed, 5 failed, 5 warnings in 11.70s
```

The five expected failures cover both single-file and batch source self-matching,
successful DB/Recycle Bin ordering, database preservation on Recycle Bin failure,
and runtime dependency declaration. Production code was not changed during this
test-writing step.

## GREEN implementation follow-up — 2026-09-07

Completed:

- Excluded the active source path from single-file and batch duplicate lookup.
- Kept already-canonical source files in place instead of renaming or recycling them.
- Reordered removal to Recycle Bin first and database commit second, with rollback on
  database errors.
- Added `send2trash==2.1.0` to `requirements.txt` and exempted the manifest from the
  repository-wide `*.txt` ignore rule so clean clones can install it.
- Removed the redundant category loop and unused `db_titles` calculation.

```text
tests/test_ingestion_safety.py: 9 passed in 4.49s
tests/: 137 passed, 5 warnings in 9.67s
```

Automated status: **GREEN**. On 2026-09-07, the project owner also confirmed the
in-place reclassification and “Gỡ bỏ” happy paths. The implementation has passed its
manual gate and is ready for final diff review; it has not been merged automatically.

## Second safety review RED follow-up — 2026-09-07

The final diff review identified catalog reconciliation and Tk main-thread dispatch
as the remaining ingestion safety gaps. Four behavior-level tests now reproduce them:

```text
tests/test_ingestion_safety.py: 7 passed, 4 failed in 8.89s
tests/: 135 passed, 4 failed, 5 warnings in 14.91s
```

Production code was not changed during this test-writing step. The implementation is
back in TDD RED until these four cases pass.

## Second safety implementation GREEN follow-up — 2026-09-07

- Cataloged sources with another physical copy remain untouched and emit a
  reconciliation warning.
- Quarantine success/failure messages are dispatched through `_safe_log()`.
- Widget removal is scheduled with `after(0, widget.destroy)`.

```text
tests/test_ingestion_safety.py: 11 passed in 5.73s
tests/: 139 passed, 5 warnings in 14.05s
```

Automated status: **GREEN**. On 2026-09-07, the project owner confirmed cataloged
duplicate preservation, reconciliation logging, and responsive normal quarantine
cleanup. The manual gate has passed; no merge was performed automatically.
