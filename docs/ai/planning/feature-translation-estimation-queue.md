---
phase: planning
title: Project Planning & Task Breakdown (Book ETA & Chapter Queue)
description: Break down work into actionable tasks and estimate timeline
---

# Project Planning & Task Breakdown

## Milestones
**What are the major checkpoints?**

- [ ] Milestone 1: Book-Level ETA Calculation & Display
- [ ] Milestone 2: Chapter Queue Logic & Background Worker
- [ ] Milestone 3: Queue UI (Add/Remove, Pause/Resume)

## Task Breakdown
**What specific work needs to be done?**

### Phase 1: Book ETA
- [ ] Task 1.1: Add `local_llm_wpm` setting to `settings.json` (default 180).
- [ ] Task 1.2: Implement `calculate_book_eta(book)` to sum untranslated words.
- [ ] Task 1.3: Upate `library_view.py` to add an ETA label next to the Webview/AI Vocab buttons at the top.

### Phase 2: Chapter Queue Logic
- [ ] Task 2.1: Create a `ChapterQueueManager` class to hold the queue state natively.
- [ ] Task 2.2: Implement the worker thread loop that pulls chapters and calls `TranslationService`.
- [ ] Task 2.3: Ensure the `TranslationService` can report progress back to the Queue Manager thread-safely.

### Phase 3: Queue UI
- [ ] Task 3.1: Add "Add to Queue" / "Remove from Queue" visual states to the chapter list in `library_view.py`.
- [ ] Task 3.2: Add global "Start Queue", "Pause Queue" buttons for the book.
- [ ] Task 3.3: Wire callbacks so the UI reflects the current queue status.

## Dependencies
**What needs to happen in what order?**

- Phase 1 is independent and can be done first.
- Phase 3 depends on Phase 2.

## Timeline & Estimates
**When will things be done?**

- Book ETA: 1 session.
- Chapter Queue: 2 sessions.

## Risks & Mitigation
**What could go wrong?**

- **Risk:** Threading issues between Queue Worker and Tkinter UI.
- **Mitigation:** Use strict `.after()` scheduling for any UI updates originating from the worker thread.
