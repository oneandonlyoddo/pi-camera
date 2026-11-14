"""PostToolUse hook (Edit|Write): run ruff on a Python file right after Claude edits it.

Exit 2 sends the findings back to Claude. The edit itself is never undone.
Missing tooling (uvx) is reported and skipped, never fatal.
"""
import json
import os
import shutil
import subprocess
import sys

data = json.load(sys.stdin)
path = (data.get("tool_input") or {}).get("file_path", "")
if not path.endswith(".py"):
    sys.exit(0)

uvx = shutil.which("uvx")
if not uvx:
    print("ruff hook skipped: uvx not found on PATH", file=sys.stderr)
    sys.exit(0)

result = subprocess.run(
    [uvx, "--quiet", "ruff", "check", "--output-format", "concise", path],
    capture_output=True,
    text=True,
    cwd=os.environ.get("CLAUDE_PROJECT_DIR") or None,
)
if result.returncode == 0:
    sys.exit(0)

print(
    f"ruff findings in {path}. Fix the ones in code you just wrote or changed; "
    "leave pre-existing ones for the refactor unless asked.\n"
    f"{result.stdout}{result.stderr}",
    file=sys.stderr,
)
sys.exit(2)
