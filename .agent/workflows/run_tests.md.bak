---
description: Procedure for running tests safely
---

# WORKFLOW: Run Tests

**Step 1: Environment Check**
- **CRITICAL**: Is venv active?
- **Command**: `.\venv\Scripts\activate`

**Step 2: Run Tests**
- **Unit Tests**:
    ```powershell
    python -m pytest tests/
    ```
- **Manual Scripts**:
    ```powershell
    python scripts/my_debug_script.py
    ```

**Step 3: Analyze Output**
- Capture the output.
- If FAILED: Stop, Fix, Retry.
- If PASSED: Copy relevant log snippet to `walkthrough.md` as proof.
