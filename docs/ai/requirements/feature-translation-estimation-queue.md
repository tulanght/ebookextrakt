---
phase: requirements
title: Requirements & Problem Understanding (Book ETA & Chapter Queue)
description: Clarify the problem space, gather requirements, and define success criteria for Book ETA and Chapter Translation Queue
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- **Translation Time Uncertainty (Book Level):** Users do not know how long it will take to translate an entire book using a Local LLM or Cloud API. Without an estimate, users can't plan their time.
- **Lack of Granular Control (Chapter Level):** Translating an entire book takes too long, and users often only need specific chapters translated. Currently, there is no way to queue specific chapters for translation and manage that queue (pause, remove).

## Goals & Objectives
**What do we want to achieve?**

- **Primary goals:**
  - **Feature 1: Book-Level ETA:** Calculate and display the Estimated Time of Arrival (ETA) to translate the *entire remaining untranslated portion* of a book. This should be displayed prominently at the top of the book details panel, near the "Đọc Thử (Webview)" and "AI Tạo Từ Vựng" buttons.
  - **Feature 2: Chapter Queue:** Implement a queue system for individual chapters/articles. Users can select which chapters to queue up for translation. The queue processes these chapters sequentially. Users can pause the queue or remove chapters from it.
- **Secondary goals:**
  - ETA calculation dynamically updates if a chapter finishes translating.

- **Future Scope:**
  - Tối ưu hóa tốc độ của Local LLM (qua các kỹ thuật quantization, batching tốt hơn).
  - Làm ETA riêng biệt cho Cloud API (Gemini/OpenAI) - hiện tại ưu tiên làm ETA chung / dựa trên Local LLM trước.

- **Non-goals:**
  - Hàng đợi xuyên suốt nhiều cuốn sách khác nhau (queue chỉ giới hạn trong phạm vi các chương của 1 cuốn sách đang mở).

## User Stories & Use Cases
**How will users interact with the solution?**

- As a user opening a book, I want to look at the top of the panel and immediately see "Estimated time to translate the rest of this book: 1h 30m".
- As a user, I want to click a button on specific chapters to add them to a "Translation Queue".
- As a user, I want the system to translate the chapters in the queue one by one automatically.
- As a user, I want to optionally pause the queue or remove a chapter from the queue if I change my mind.

## Success Criteria
**How will we know when we're done?**

- A visible ETA string appears at the top of the book panel (e.g., next to the Webview button).
- Users can queue specific chapters.
- The system translates queued chapters sequentially in the background.
- Pausing/removing items from the queue works without crashing the app.

## Constraints & Assumptions
**What limitations do we need to work within?**

- **Assumptions:** We will use a Word-Per-Minute (WPM) constant to calculate the ETA (e.g., based on User's benchmark of 1370 words in 7-8 minutes -> ~180 WPM).
- **Constraints:** The UI must remain responsive while the queue is processing.

## Questions & Open Items
**What do we still need to clarify?**

- None at the moment.
