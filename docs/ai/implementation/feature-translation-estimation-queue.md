---
phase: implementation
title: Implementation Guide (Book ETA & Chapter Queue)
description: Technical implementation notes, patterns, and code guidelines
---

# Implementation Guide

## Code Structure
**How is the code organized?**

- **Settings:** `local_llm_wpm` in `settings.json`.
- **Core Logic:** `calculate_book_eta` utility in `src/extract_app/core/utils/` (or similar).
- **Queue Manager:** A new native class/module for `ChapterQueueManager`.
- **UI Modifications:** Inside `src/extract_app/modules/ui/library_view.py`.

## Implementation Notes
**Key technical details to remember:**

### Book ETA Strategy
- Find the `active_book`. Sum the `word_count` (or approximate words from char counts) for all chapters where `translated == False`.
- ETA = `total_words / local_llm_wpm`.
- Format as `%H:%M`.
- Add a new `CTkLabel` in the top frame of the Book Details view (the header area containing "Đọc Thử (Webview)" and "AI Tạo Từ Vựng").

### Chapter Queue Strategy
- At the chapter level, visually add checkboxes or "Add to Queue" toggles next to the "Dịch Lại" / "Biên tập" buttons.
- `ChapterQueueManager` runs a `threading.Thread` loop. It maintains a list of `chapter_ids`.

## Error Handling
**How do we handle failures?**

- ETA handles division by zero or missing `word_count` gracefully by showing "ETA: N/A".
- The Queue loop catches `Exception` per chapter to avoid killing the worker thread if a single translation fails.
