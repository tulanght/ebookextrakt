# AI DevKit Rules

## Project Context
This project uses ai-devkit for structured AI-assisted development. Phase documentation is located in `docs/ai/`.

## Documentation Structure
- `docs/ai/requirements/` - Problem understanding and requirements
- `docs/ai/design/` - System architecture and design decisions (include mermaid diagrams)
- `docs/ai/planning/` - Task breakdown and project planning
- `docs/ai/implementation/` - Implementation guides and notes
- `docs/ai/testing/` - Testing strategy and test cases
- `docs/ai/deployment/` - Deployment and infrastructure docs
- `docs/ai/monitoring/` - Monitoring and observability setup

## Code Style & Standards — ExtractPDF-EPUB Specifics

### Environment Constraints
- **VENV ACTIVATION**: You MUST activate the virtual environment before running ANY Python command.
    - Windows: `.\venv\Scripts\activate` (or run python via `.\venv\Scripts\python.exe`)
- **NO GLOBAL PIP**: Never install packages globally. Always ensure venv is active.

### Git Workflow
- **NEVER COMMIT TO MAIN**: You must be on a `feature/` or `fix/` branch.
- **Branch Naming**: `feature/<name>`, `fix/<name>`, `docs/<name>`, `exp/<name>`
- **Conventional Commits**: `<type>(<scope>): <subject>`
- **ATOMIC COMMITS**: One logical change per commit.
- **DOCUMENTATION MANDATE**: Before closing a task, update:
    - `CHANGELOG.md` (what changed)
    - `ROADMAP.md` (mark features as `[x]`)
- **NO LARGE FILES**: Files > 50MB are FORBIDDEN. Add them to `.gitignore`.
- **CLEANUP**: Remove `temp/`, `Output/`, and debug scripts before pushing.
- **PRE-CHECK**: Run `git status` to verify no large files are staged.

### Python Coding Standards
Every Python file MUST start with this header block:
```python
# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: <filename>
# Version: <version>
# Author: Antigravity
# Description: <Short description of what this file does>
# --------------------------------------------------------------------------------
```

- **Docstrings (Google Style)**: Required for all modules, classes, and functions.
- **Type Hints**: Required for all new code. Use `typing` module.
- **Versioning**: Maintain `__version__ = "x.y.z"` in module `__init__.py` files.

### Verification
- **STRICT VERIFICATION**: Run automated scripts → Ask user to manually verify (`notify_user`) → ONLY merge after user says "OK".
- **SHOW THE LOGS**: Don't just say "it works". Provide evidence in `walkthrough.md`.

## Skills (Extend Your Capabilities)
Skills are packaged capabilities that teach you new competencies, patterns, and best practices. Check for installed skills in the project's skill directory and use them to enhance your work.

### Using Installed Skills
1. **Check for skills**: Look for `SKILL.md` files in the project's skill directory
2. **Read skill instructions**: Each skill contains detailed guidance on when and how to use it
3. **Apply skill knowledge**: Follow the patterns, commands, and best practices defined in the skill

### Key Installed Skills
- **memory**: Use AI DevKit's memory service via CLI commands when MCP is unavailable. Read the skill for detailed `memory store` and `memory search` command usage.

### When to Reference Skills
- Before implementing features that match a skill's domain
- When MCP tools are unavailable but skill provides CLI alternatives
- To follow established patterns and conventions defined in skills

## Knowledge Memory (Always Use When Helpful)
The AI assistant should proactively use knowledge memory throughout all interactions.

> **Tip**: If MCP is unavailable, use the **memory skill** for detailed CLI command reference.

### When to Search Memory
- Before starting any task, search for relevant project conventions, patterns, or decisions
- When you need clarification on how something was done before
- To check for existing solutions to similar problems
- To understand project-specific terminology or standards

**How to search**:
- Use `memory.searchKnowledge` MCP tool with relevant keywords, tags, and scope
- If MCP tools are unavailable, use `npx ai-devkit memory search` CLI command (see memory skill for details)
- Example: Search for "authentication patterns" when implementing auth features

### When to Store Memory
- After making important architectural or design decisions
- When discovering useful patterns or solutions worth reusing
- If the user explicitly asks to "remember this" or save guidance
- When you establish new conventions or standards for the project

**How to store**:
- Use `memory.storeKnowledge` MCP tool
- If MCP tools are unavailable, use `npx ai-devkit memory store` CLI command (see memory skill for details)
- Include clear title, detailed content, relevant tags, and appropriate scope
- Make knowledge specific and actionable, not generic advice

### Memory Best Practices
- **Be Proactive**: Search memory before asking the user repetitive questions
- **Be Specific**: Store knowledge that's actionable and reusable
- **Use Tags**: Tag knowledge appropriately for easy discovery (e.g., "api", "testing", "architecture")
- **Scope Appropriately**: Use `global` for general patterns, `project:<name>` for project-specific knowledge

## Testing & Quality
- Write tests alongside implementation
- Follow the testing strategy defined in `docs/ai/testing/`
- Use `/writing-test` to generate unit and integration tests targeting 100% coverage
- Ensure code passes all tests before considering it complete

## Documentation
- Update phase documentation when requirements or design changes
- Keep inline code comments focused and relevant
- Document architectural decisions and their rationale
- Use mermaid diagrams for any architectural or data-flow visuals (update existing diagrams if needed)
- Record test coverage results and outstanding gaps in `docs/ai/testing/`

## Key Commands
When working on this project, you can run commands to:
- Understand project requirements and goals (`review-requirements`)
- Review architectural decisions (`review-design`)
- Plan and execute tasks (`execute-plan`)
- Verify implementation against design (`check-implementation`)
- Writing tests (`writing-test`)
- Perform structured code reviews (`code-review`)

### 🤖 TRỢ LÝ ĐIỀU HƯỚNG QUY TRÌNH (WORKFLOW NAVIGATOR)
**Chỉ thị bắt buộc:** Ở cuối MỖI câu trả lời, bạn (Antigravity) BẮT BUỘC phải chủ động gợi ý bước tiếp theo bằng một Slash Command phù hợp của AI DevKit (ví dụ: `/writing-test`, `/check-implementation`, `/remember`, v.v.).

**Định dạng xuất bắt buộc (Luôn đặt ở cuối cùng):**
---
💡 **Gợi ý bước tiếp theo:** Nhập `[tên_lệnh_phù_hợp]` nếu bạn muốn tôi [mô tả ngắn gọn lợi ích của lệnh này].
