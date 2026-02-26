---
phase: design
title: System Design & Architecture
description: Define the technical architecture, components, and data models
---

# System Design & Architecture

## Architecture Overview
**What is the high-level system structure?**

- Include a mermaid diagram that captures the main components and their relationships. Example:
  ```mermaid
  graph TD
    Client -->|HTTPS| API
    API --> ServiceA
    API --> ServiceB
    ServiceA --> Database[(DB)]
  ```
- Key components and their responsibilities
- Technology stack choices and rationale

## Data Models
**What data do we need to manage?**

- Core entities and their relationships
- Data schemas/structures
- Data flow between components

## API Design
**How do components communicate?**

- External APIs (if applicable)
- Internal interfaces
- Request/response formats
- Authentication/authorization approach

## Component Breakdown
**What are the major building blocks?**

- Frontend components (if applicable)
- Backend services/modules
- Database/storage layer
- Third-party integrations

## Design Decisions — ExtractPDF-EPUB Architectural History
**Why did we choose this approach?**

### Decision 1: Recursive EPUB ToC Parsing + Relative Path Resolution
- **Problem**: EPUB files from different sources have wildly inconsistent ToC structures (Link, tuple, Section objects) and image paths are almost always relative (`../images/...`).
- **Failed approaches (v2.x–v11.x)**: Assumed ToC only contains `Link`/`tuple`; assumed content at direct `<body>` children; assumed absolute image paths.
- **Final approach (v12.0+)**:
  - Recursive deep traversal of any iterable object in ToC (handles `Link`, `tuple`, `Section`).
  - `os.path.normpath` to resolve relative paths before image lookup.
  - `soup.body.find_all(...)` for flat, sequential extraction of all content tags.

### Decision 2: Image Anchor System (Performance)
- **Problem**: Rendering hundreds of real images in CustomTkinter caused UI freeze/crash (`_tkinter.TclError: row out of bounds`).
- **Decision**: The UI is a **data verification tool**, not an ebook reader. Parser saves images to `/temp` directory and returns only the file path (anchor). UI displays path strings only.
- **Result**: Eliminated all performance issues.

### Decision 3: filedialog Workaround
- **Problem**: `filedialog.askdirectory` crashes with `_tkinter.TclError: Unspecified error` due to deep conflict between Python/tkinter/customtkinter/Windows.
- **Decision**: Replaced `filedialog` entirely with a `CTkEntry` field where users paste directory paths manually. Prioritizes **stability** over convenience.

## Non-Functional Requirements
**How should the system perform?**

- Performance targets: Handle EPUB/PDF files with 100+ chapters and 500+ images without UI freeze
- Scalability: Support batch extraction of multiple files
- Security: No external network calls during extraction; all processing is local
- Reliability: Graceful handling of malformed EPUB/PDF structures with logging

