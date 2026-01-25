---
description: Procedure for finishing a task and merging
---

# WORKFLOW: Finish Task

**Step 1: Verification Check**
- Have all new files been checked against `coding_standards.md`?
- Have tests been run and logged in `walkthrough.md`?

**Step 2: Changelog**
- **Action**: Update `CHANGELOG.md` at the project root.
- **Format**: Follow existing pattern (Version, Date, Added/Fixed).

**Step 3: Commit & Push**
- **Command**:
    ```powershell
    git add .
    git commit -m "type(scope): description"
    # Wait for user approval to push if needed, or just commit locally.
    ```

**Step 4: Notify User**
- Use `notify_user` to request final review.
- Mention: "Task Complete. Branch ready for review/merge."
