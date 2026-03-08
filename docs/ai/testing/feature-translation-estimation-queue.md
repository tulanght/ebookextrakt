---
phase: testing
title: Testing Strategy (Book ETA & Chapter Queue)
description: Define testing approach, test cases, and quality assurance
---

# Testing Strategy

## Unit Tests
**What individual components need testing?**

### ETA Logic
- [x] Test `calculate_book_eta` accurately sums untranslated chapters only and applies WPM calculation.
  - *Implemented in [`tests/test_eta_calculator.py`](../../../tests/test_eta_calculator.py)*

### Queue Manager Logic
- [x] Test adding/removing items to `QueueManager`.
- [x] Test that the background worker pulls items sequentially and fires callbacks.
  - *Implemented in [`tests/test_queue_manager.py`](../../../tests/test_queue_manager.py)*

## End-to-End Tests
**What user flows need validation?**

- [ ] **Book ETA Display:** Open a book. Notice the ETA label at the top. Open a book that is 100% translated, the ETA should say 0 or "Complete".
- [ ] **Queue Flow:** Check 3 chapters. Click "Start Queue". Watch 3 chapters translate sequentially without UI locking.
- [ ] **Queue Pause:** Pause the queue. Verify the current chapter finishes and the next one does not start.

## Manual Testing
**What requires human validation?**

- **Visual Alignment:** Ensure the ETA text fits comfortably next to the Webview / AI Vocab buttons without pushing them off-screen or looking misaligned.
- **UI Responsiveness:** Ensure the app does not freeze (`Not Responding`) when the queue is running a heavy Local LLM task.
