---
description: GLOBAL RULES - READ THIS FIRST
---

# PROJECT RULES & CONSTRAINTS

> [!CRITICAL]
> THESE RULES ARE NON-NEGOTIABLE.
> VIOLATION = FAILURE.

## 1. Environment & Execution
- **VENV ACTIVATION**: You MUST explicitly activate the virtual environment before running ANY python command.
    - Windows: `.\venv\Scripts\activate` (or run python via `.\venv\Scripts\python.exe`)
- **NO GLOBAL PIP**: Never install packages globally. Always ensure venv is active.

## 2. Git & Workflow
- **NEVER COMMIT TO MAIN**: You must be on a `feature/` or `fix/` branch.
- **ATOMIC COMMITS**: One logical change per commit.
- **CHANGELOG**: You MUST update `CHANGELOG.md` before finishing a task.
- **GIT CONSTRAINTS**:
    - **NO LARGE FILES**: Files > 50MB are FORBIDDEN. Add them to `.gitignore`.
    - **CLEANUP**: Remove `temp/`, `Output/`, and debug scripts before pushing.
    - **PRE-CHECK**: Run `git status` to verify no large files are staged.

## 3. Coding Standards
- **READ STANDARDS**: Before writing any code, read `.agent/workflows/coding_standards.md`.
- **DOCSTRINGS**: Required for all modules, classes, and functions.
- **TYPE HINTS**: Required for all new code.

## 4. Interaction
- **ARTIFACTS**: Use `task.md` to track progress.
- **VERIFICATION**: Don't just say "it works". SHOW THE LOGS in `walkthrough.md`.
