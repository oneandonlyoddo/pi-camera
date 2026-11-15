---
name: commit
description: Split the finished work of a feature request into small, related, working commits with short messages, and commit them locally (never push). Use only when the user asks to commit ("commit this", "/commit", "I'm happy with it, commit").
disable-model-invocation: true
---

# Commit finished work

The user runs this when they are happy with a feature. Turn the uncommitted changes into a series of small commits on the **current branch**. Never push.

## 1. Inventory

- `git status --short`, `git diff --stat`, `git diff` (and `git diff --cached` if anything is staged already).
- `git log --format='%h %s' -15` for the message style.
- Never commit: `DCIM/`, `device-out/`, `camera_settings.json`, `.claude/settings.local.json`, scratch files. They are git-ignored; if one shows up anyway, stop and tell the user.
- **Changes not from this feature** (e.g. the user's own edits to design docs or reference images): list them and ask whether to include them, as their own commit, or leave them uncommitted.

## 2. Group into commits

Group hunks, not just files, by:
1. **Relation:** one commit = one idea a reader can review alone (e.g. "state + persistence", "touch positions", "menu UI", "HUD redesign").
2. **Order of implementation:** follow the order the work was done in the conversation. If that is unknown, follow dependencies (helpers before their callers).

Rules for every commit:
- **It works on its own.** Every import and name it uses exists in that commit or an earlier one, tests that cover its code come with it, and no commit leaves a caller pointing at a removed name. If two parts only work together, they are one commit.
- **Docs ship with the code (R9).** README, CLAUDE.md, `docs/`, `.claude/` changes go into the commit whose behaviour they describe, not a separate docs commit. Pure doc fixes may be their own commit.
- One file may be split across commits by hunk. If one hunk mixes two ideas, keep it in the commit it needs to work.
- Prefer 2–6 commits. Do not split below a meaningful unit.

## 3. Propose, then ask once

Show the plan as a numbered list: message, then files (with "partial" for split files) and a few words on what goes in. Ask once whether to go ahead (AskUserQuestion: go ahead / adjust). Apply their changes to the plan; do not ask again for each commit.

## 4. Commit, one at a time

For each commit, in order:

1. **Stage exactly its content.**
   - Whole files: `git add -- <files>` (deleted files: `git rm --cached -- <file>` or `git add -A -- <file>`).
   - Part of a file: no interactive git here (`git add -p` doesn't work). Write a patch with only the wanted hunks to the scratchpad (from `git diff -U3 -- <file>`, keeping the file header), then `git apply --cached --recount <patch>`. Check with `git diff --cached -- <file>`.
2. **Check that the staged snapshot works:** export it and lint it:
   ```bash
   rm -rf "<scratchpad>/snap" && mkdir -p "<scratchpad>/snap" && git checkout-index -a --prefix="<scratchpad>/snap/"
   uvx --quiet ruff@0.17.5 check "<scratchpad>/snap"
   ```
   ruff catches broken imports and undefined names (F401/F821). Also grep the snapshot for names the commit removes. If anything fails, fix the grouping (move hunks between commits), never the code.
3. **Commit** with the message in a file: `git commit -F <scratchpad>/msg.txt`.
   - Subject: `Area: what changed`, imperative, ≤ 60 characters, like the existing log (`Camera: ...`, `Web: ...`, `HUD: ...`, `Docs: ...`, `Harness: ...`).
   - Body only if needed: one or two lines on why, citing rule IDs (R2, R8, R11...).
   - End with the attribution trailer Claude Code requires for commits in this session, if any.
   - Never `--no-verify`, never `--amend` an existing commit, never rewrite history.
4. Go to the next commit. At the end `git status --short` must be empty, apart from what the user chose to leave uncommitted.

## 5. Report

`git log --oneline -<n>` of the new commits, and what was left uncommitted and why. Only the final state was tested on the Pi (R10); intermediate commits are checked statically (ruff on each snapshot). Say so. Do not push.
