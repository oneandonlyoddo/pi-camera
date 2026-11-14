"""PreToolUse hook: two guard rails, checked before every tool call.

1. Photos (R11): block anything that could delete, move or overwrite DCIM/.
   A command is blocked when it mentions "dcim" anywhere (any case) AND
   contains a destructive word anywhere. Harmless combinations such as
   `rm -rf device-out && ls DCIM` are blocked too; that is intended.
2. Project boundary: block file tools and shell commands that point outside
   the project (home folder references, absolute paths elsewhere, `..` that
   leaves the project). Allowed outside the project: the session scratchpad
   (Temp/claude), Claude's own folder for this project, and reading
   installed plugin files. In `ssh ...` commands, `~` and `$HOME` refer to
   the Pi and are not checked.

Exit 2 blocks the call and tells Claude why. Any internal error also exits 2
(fail closed). These are guard rails for obvious cases, not a sandbox.
"""
import json
import os
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
HOME = Path(os.path.expanduser("~"))
READ_TOOLS = {"Read", "Glob", "Grep"}


def norm(p):
    return os.path.normcase(os.path.abspath(p))


def allowed_roots(tool):
    slug = re.sub(r"[:\\/]", "-", str(PROJECT))
    roots = [
        PROJECT,
        HOME / "AppData" / "Local" / "Temp" / "claude",  # session scratchpad
        HOME / ".claude" / "projects" / slug,  # Claude's saved tool output for this project
    ]
    if tool in READ_TOOLS:
        roots.append(HOME / ".claude" / "plugins")  # plugin skill files
    return [norm(r) for r in roots]


def inside(path, roots):
    p = norm(path)
    return any(p == r or p.startswith(r + os.sep) for r in roots)


def block(reason):
    print(f"Blocked by .claude/hooks/guard.py: {reason}", file=sys.stderr)
    sys.exit(2)


# --- 1. photos ---------------------------------------------------------------

DESTRUCTIVE = re.compile(
    r"\b(rm|rmdir|mv|del|erase|rd|shred|truncate|unlink|rmtree|remove|rename|replace|move|"
    r"Remove-Item|Move-Item|Rename-Item|Clear-Content|Set-Content|Out-File|Copy-Item|cp|scp)\b"
    r"|>{1,2}(?!\s*(/dev/null|&\d|\$null))"  # redirects, except to /dev/null or another stream
    r"|-delete\b",
    re.IGNORECASE,
)
# These remove git-ignored files, which includes DCIM/, without ever naming it.
GIT_IGNORED_WIPE = re.compile(r"\bgit\s+clean\b[^\n]*\s-[a-zA-Z]*[xX]|\bgit\s+stash\b[^\n]*\s(-a\b|--all\b)")


def check_photos(tool, tool_input):
    if tool in ("Edit", "Write", "NotebookEdit"):
        path = (tool_input.get("file_path") or tool_input.get("notebook_path") or "").replace("\\", "/")
        if re.search(r"(^|/)dcim(/|$)", path, re.IGNORECASE):
            block(f"R11: {tool} on {path}. DCIM/ holds the user's photos.")
    command = tool_input.get("command") or ""
    if GIT_IGNORED_WIPE.search(command):
        block("R11: this git command deletes git-ignored files, which includes DCIM/ (the user's photos).")
    if re.search(r"dcim", command, re.IGNORECASE) and DESTRUCTIVE.search(command):
        block(
            "R11: command mentions DCIM and contains a delete/move/write operation. "
            "DCIM/ holds the user's photos. Rephrase without touching DCIM, or ask the user to run it."
        )


# --- 2. project boundary -----------------------------------------------------

HOME_REFS = re.compile(
    r"(^|[\s'\"=(;&|])~(?=$|[/\\\s'\"])"
    r"|\$HOME\b|\$\{HOME\}|%USERPROFILE%|%APPDATA%|%LOCALAPPDATA%|%HOMEPATH%"
    r"|\$env:(USERPROFILE|HOME|APPDATA|LOCALAPPDATA)\b",
    re.IGNORECASE,
)
WIN_ABS = re.compile(r"(?<![\w/])([A-Za-z]:[\\/][^\s'\"|;&<>]*)")
BASH_DRIVE_ABS = re.compile(r"(?<![\w.:/-])/([a-zA-Z])(/[^\s'\"|;&<>]*)")


def check_path(tool, raw, cwd, roots):
    path = raw if os.path.isabs(raw) else os.path.join(cwd, raw)
    if not inside(path, roots):
        block(f"{tool} on {raw}, which is outside the project ({PROJECT}). Ask the user first.")


def check_boundary(tool, tool_input, cwd):
    roots = allowed_roots(tool)
    for key in ("file_path", "notebook_path", "path"):
        raw = tool_input.get(key)
        if raw:
            check_path(tool, raw, cwd, roots)

    command = tool_input.get("command") or ""
    if not command:
        return
    if not re.match(r"\s*ssh\s", command) and HOME_REFS.search(command):
        block("command refers to the home folder, which is outside the project. Ask the user first.")
    for raw in WIN_ABS.findall(command):
        check_path(tool, raw, cwd, roots)
    for drive, rest in BASH_DRIVE_ABS.findall(command):
        check_path(tool, f"{drive}:{rest}", cwd, roots)
    for token in re.split(r"[\s'\"=;&|<>()]+", command):
        if ".." in re.split(r"[\\/]", token):
            check_path(tool, token, cwd, roots)


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    check_photos(tool, tool_input)
    check_boundary(tool, tool_input, cwd)


try:
    main()
except SystemExit:
    raise
except Exception as e:  # fail closed: a broken guard must not let calls through
    block(f"guard error ({type(e).__name__}: {e}); call blocked to be safe. Fix the hook or ask the user.")
sys.exit(0)
