"""PostToolUse hook (Edit|Write): run ruff on a Python file right after Claude edits it.

Exit 2 sends real findings back to Claude. The edit itself is never undone.
If ruff cannot run (uvx missing, offline, download error), the hook skips quietly:
uvx and ruff both use exit code 1, so findings are recognised by ruff's
"Found N error" summary line, not by the exit code.
"""
import json
import os
import re
import shutil
import subprocess
import sys

RUFF = "ruff@0.17.5"  # pinned so rules and output do not change under us

data = json.load(sys.stdin)
path = (data.get("tool_input") or {}).get("file_path", "")
if not path.endswith(".py"):
    sys.exit(0)

uvx = shutil.which("uvx")
if not uvx:
    print("ruff hook skipped: uvx not found on PATH", file=sys.stderr)
    sys.exit(0)

result = subprocess.run(
    [uvx, "--quiet", RUFF, "check", "--output-format", "concise", path],
    capture_output=True,
    text=True,
    cwd=os.environ.get("CLAUDE_PROJECT_DIR") or None,
)
if result.returncode == 0 or not re.search(r"^Found \d+ errors?\b", result.stdout, re.MULTILINE):
    if result.returncode != 0:
        print(f"ruff hook skipped: ruff did not run ({result.stderr.strip()[:200]})", file=sys.stderr)
    sys.exit(0)

print(f"ruff findings in {path}. Fix the ones in code you just wrote or changed.\n{result.stdout}", file=sys.stderr)
sys.exit(2)
