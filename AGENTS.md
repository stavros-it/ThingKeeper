# AGENTS.md

> Instructions for AI assistants (and human contributors) working on ThingKeeper.

## Workflow rules

When making any change to the codebase — bug fix, feature, refactor, docs —
**always** do the following before considering the task complete:

1. **Update `PROJECT_CONTEXT.md`** to reflect the new state:
   - File tree (add new files, update descriptions)
   - Architecture diagrams if they changed
   - Conventions (new patterns introduced)
   - Known limitations (new gotchas)
   - The "Where to make changes" table (new modules / entry points)

2. **Update `ROADMAP.md`**:
   - Mark relevant items as **Done** (move from "Planned" to current state)
   - Add new planned items under the appropriate version section
   - Move anything rejected to "Dropped / not doing" with a reason

3. **Run quality checks** before committing:
   ```powershell
   ruff check .
   ```
   Must pass. Fix any issues before proceeding.

   (A `tests/` suite is planned for v1.0 — once added, `python -m pytest tests/ -q`
   becomes a required check too.)

4. **Commit and push** to the GitHub repo:
   ```powershell
   git add -A
   git commit -m "<concise message matching repo style>"
   git push
   ```
   The remote is `https://github.com/stavros-it/ThingKeeper.git` (already
   configured as `origin` on the `main` branch).

5. **Check the latest CI run** after pushing (once CI is configured):
   CI is not yet set up for ThingKeeper. Once a `.github/workflows/ci.yml`
   is added (planned in ROADMAP v1.0), verify the latest run is green:
   ```powershell
   curl -s https://api.github.com/repos/stavros-it/ThingKeeper/commits/$(git rev-parse HEAD)/check-runs | python -m json.tool
   ```
   - If the CI **passes**, the task is complete.
   - If the CI **fails**, read the error output, fix the issue locally
     (tests, lint, platform-specific code), and push a new commit. Repeat
     until the latest CI run is green.

   Common CI failures on Linux that don't show on Windows:
   - Platform-specific code paths (e.g. `os.path.splitdrive`, `sys.platform`)
   - `PermissionError` vs `IsADirectoryError` when writing to directories
   - Windows API calls (`ctypes.windll`) not guarded by `sys.platform == "win32"`
   - Path separators and drive-letter assumptions in tests

## Pre-push safety check

Before every commit/push, verify that **no secrets or user data** are staged:

```powershell
git ls-files          # tracked files (must NOT include *.db, *.xlsx, data/)
git diff --cached --name-only
```

Local-only, git-ignored files that must never be committed:
- `data/thingkeeper.db` (your inventory) — gitignored, local-only
- `data/attachments/` (item images) — gitignored, local-only
- `My Equipment.xlsx` (source spreadsheet with personal data) — gitignored, local-only
- `*.tkz`, `*.csv`, `*.pdf`, `*.log` (export artifacts) — gitignored

If any of these appear in `git ls-files`, **do not push** — fix `.gitignore`
first and `git rm --cached` the file.

## Commit message style

- Imperative mood: "Add loan tracking", not "Added loan tracking"
- First line ≤ 72 chars, optionally followed by a blank line and body
- Reference the feature/bug in the first line; details go in the body
- Examples from this repo's history:
  - `Initial ThingKeeper app: PyQt6 + SQLite inventory manager`
  - `Add launch.pyw for console-free launch on Windows`

## Code conventions

- **No comments** in code unless explicitly requested
- **Type hints** everywhere; `from __future__ import annotations` at module top
- **No emojis** in source, docs, or UI strings unless explicitly requested
- **No hardcoded hex colors** in UI code — centralise in a theme module if
  theming grows (currently a small `STATUS_COLORS` dict in `main_window.py`)
- **No network calls** — ThingKeeper is offline-first; importers/exporters
  read local files only
- **Dates stored as ISO text** (`YYYY-MM-DD`) in SQLite, normalised on import

## Repo details

- **Remote**: `origin` → `https://github.com/stavros-it/ThingKeeper.git`
- **Default branch**: `main`
- **License**: Proprietary (© 2026 Stavros Antoniou, all rights reserved)
- **CI**: Not yet configured (planned in ROADMAP v1.0)
- **Entry points**: `main.py` (console), `launch.pyw` (no console on Windows),
  `python -m thingkeeper`
