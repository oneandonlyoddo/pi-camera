"""PreToolUse hook: block anything that would delete, move or overwrite photos (R11).

Covers Edit/Write on DCIM/ paths and shell commands (local or via ssh) that
combine a destructive verb with DCIM. Exit 2 blocks the call and tells Claude why.
This is a guard rail for obvious cases, not a sandbox.
"""
import json
import re
import sys

data = json.load(sys.stdin)
tool = data.get("tool_name", "")
tool_input = data.get("tool_input") or {}

REASON = "Blocked by R11: DCIM/ holds the user's photos and must not be deleted, moved or overwritten."


def block(detail):
    print(f"{REASON} ({detail}) Ask the user to do it themselves if it is really needed.", file=sys.stderr)
    sys.exit(2)


if tool in ("Edit", "Write", "NotebookEdit"):
    path = (tool_input.get("file_path") or tool_input.get("notebook_path") or "").replace("\\", "/")
    if re.search(r"(^|/)DCIM(/|$)", path):
        block(f"{tool} on {path}")
    sys.exit(0)

command = tool_input.get("command") or ""
SEGMENT = r"[^;&|\n]*"  # stay within one command of a chain
patterns = {
    "destructive command on DCIM": rf"\b(rm|rmdir|mv|shred|truncate|unlink|del|rd|Remove-Item|Move-Item|Rename-Item|Clear-Content|Set-Content|Out-File)\b{SEGMENT}DCIM",
    "redirect into DCIM": r">{1,2}\s*['\"]?[^\s;&|'\"]*DCIM/",
    "find -delete in DCIM": rf"DCIM{SEGMENT}-delete\b",
    "copy into DCIM": rf"\b(cp|scp|Copy-Item)\b{SEGMENT}\s['\"]?[^\s;&|'\"]*DCIM[^\s;&|'\"]*['\"]?\s*($|[;&|\n])",
    "git clean -x (DCIM is git-ignored)": r"\bgit\s+clean\b[^;&|\n]*\s-[a-zA-Z]*[xX]",
}
for detail, pattern in patterns.items():
    if re.search(pattern, command):
        block(detail)
sys.exit(0)
