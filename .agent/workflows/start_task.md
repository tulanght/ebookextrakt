---
description: Procedure for starting a new task
---

# WORKFLOW: Start Task

**Step 1: Check Context**
- Read `.agent/workflows/project_rules.md` to refresh memory on constraints.
- Run `git status` to ensure clean state.

**Step 2: Create Branch**
- **Requirements**:
    - Branch name format: `feature/<name>` or `fix/<name>`.
    - Base: `main` (unless stacking features).
- **Command**:
    ```powershell
    git checkout main
    git pull origin main
    git checkout -b <branch_name>
    ```

**Step 3: Setup Artifacts**
- Create/Update `task.md` with the checklist.
- Create `implementation_plan.md` for the design.

**Step 4: Confirm**
- Notify user that environment is ready and planning has started.
