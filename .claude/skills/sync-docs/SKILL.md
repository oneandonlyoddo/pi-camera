---
name: sync-docs
description: Check README.md, CLAUDE.md, docs/ and the harness (.claude/) against the actual code and fix documentation drift. Use when the user asks to sync, check or update the docs, after a refactor, or before a commit that changed settings, routes, files, dependencies or scripts.
---

# Sync docs with code

The code is the source of truth. This skill fixes **docs**, not code. If the code looks wrong rather than the docs, report it instead of changing either.

## Checks

Go through each, and note every mismatch with file and line:

1. **Settings:** every constant in `settings.py` vs README "Configuration" (names, values, comments). No documented setting that does not exist.
2. **API:** every route in `web/app.py` (method, path, status codes, payload) vs README "API Reference", the route table in CLAUDE.md, and `tests/test_web.py`.
3. **Files:** the actual tree (`git ls-files -co --exclude-standard`) vs README "File Structure" and CLAUDE.md file mentions.
4. **Dependencies:** apt package lists in README, CLAUDE.md, `requirements.txt` and rule R1 agree with each other and with the imports in the code.
5. **Dev loop:** modes in `scripts/dev.sh` vs README "Development Workflow", CLAUDE.md, the `/on-device` skill, and permission rules in `.claude/settings.json`. The excluded-from-copy list matches the `grep -zvE` line.
6. **Known issues:** each entry in CLAUDE.md and README is still true in the code. Each `xfail` test in `tests/` names a known issue that still exists, and vice versa where a test is possible.
7. **Features:** `docs/FEATURES.md` statuses match the code (`done` features exist, removed ones are gone).
8. **Harness references:** files, functions and settings named in `.claude/rules/*.md` and `.claude/skills/**` exist.

## Fix

- Fix every mismatch in the docs. Keep each doc's existing structure and tone.
- Do not invent targets or hardware facts in `docs/SPECS.md` or design docs; list the gaps for the user instead.

## Report

- fixed: one line per fix
- code issues found (not fixed): one line each
- gaps the user has to fill (SPECS, design docs)
