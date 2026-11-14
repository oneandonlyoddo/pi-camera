"""Tests for guard.py. Desktop only: uvx --quiet --with pytest pytest -q -p no:cacheprovider .claude/hooks"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).with_name("guard.py")
PROJECT = GUARD.resolve().parents[2]
HOME = Path(os.path.expanduser("~"))


def run(tool, cwd=PROJECT, raw=None, **tool_input):
    stdin = raw if raw is not None else json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd)})
    return subprocess.run([sys.executable, str(GUARD)], input=stdin, capture_output=True, text=True).returncode


BLOCKED_COMMANDS = [
    # photos
    "rm -rf DCIM",
    "cd DCIM && rm *.jpg",
    'ssh pi "cd workspace/pi-camera/DCIM; rm -f IMG_*"',
    "mv DCIM/a.jpg somewhere",
    "echo x > DCIM/a.jpg",
    "find DCIM -name x -delete",
    "git clean -fdx",
    "git stash --all",
    'python -c "import shutil; shutil.rmtree(\'DCIM\')"',
    "scp test.jpg pi:pi-camera/DCIM/IMG_1.jpg",
    "rm -rf device-out && ls DCIM",  # deliberate false positive
    # project boundary
    "cat ~/.ssh/config",
    "ls ~",
    "cat $HOME/.bashrc",
    "type %USERPROFILE%\\notes.txt",
    "Get-Content $env:USERPROFILE\\notes.txt",
    "cat /c/Users/someone/secret.txt",
    "cat c:/Windows/win.ini",
    "cat ../../outside.txt",
    "cd .. && ls",
]
ALLOWED_COMMANDS = [
    "scripts/dev.sh --check",
    "scripts/dev.sh --shoot",
    "ls -t DCIM | head",
    "ssh pi 'ls -t workspace/pi-camera/DCIM/*.jpg 2>/dev/null | head -1'",
    "ssh pi 'ls ~/workspace'",  # ~ is on the Pi
    "rm -rf device-out",
    "git clean -n",
    "git log --oneline HEAD~3..HEAD",
    "git diff HEAD~1",
    f"cd \"{PROJECT.as_posix()}\" && git status",
    "curl -fsS http://localhost:5000/api/photos",
    "uvx --quiet ruff check main.py",
    "sed -i 's/a/b/' README.md",
]


@pytest.mark.parametrize("command", BLOCKED_COMMANDS)
def test_command_blocked(command):
    assert run("Bash", command=command) == 2


@pytest.mark.parametrize("command", ALLOWED_COMMANDS)
def test_command_allowed(command):
    assert run("Bash", command=command) == 0


def test_powershell_case_insensitive_dcim():
    assert run("PowerShell", command="Remove-Item dcim -Recurse") == 2


@pytest.mark.parametrize(
    "tool, path, expected",
    [
        ("Write", PROJECT / "DCIM" / "a.jpg", 2),
        ("Edit", PROJECT / "dcim" / "a.jpg", 2),
        ("Read", HOME / ".ssh" / "config", 2),
        ("Write", HOME / "notes.txt", 2),
        ("Grep", HOME, 2),
        ("Write", HOME / ".claude" / "plugins" / "x.md", 2),  # plugins are read-only
        ("Read", PROJECT / "main.py", 0),
        ("Read", "main.py", 0),  # relative to cwd = project
        ("Write", PROJECT / "tests" / "test_x.py", 0),
        ("Read", HOME / "AppData" / "Local" / "Temp" / "claude" / "x" / "out.txt", 0),
        ("Read", HOME / ".claude" / "plugins" / "cache" / "x" / "SKILL.md", 0),
        ("Read", HOME / ".claude" / "projects" / str(PROJECT).replace(":", "-").replace("\\", "-").replace("/", "-") / "tool-results" / "x.txt", 0),
    ],
)
def test_file_tools(tool, path, expected):
    key = "path" if tool == "Grep" else "file_path"
    assert run(tool, **{key: str(path)}) == expected


def test_relative_path_from_subfolder_cannot_escape():
    assert run("Read", cwd=PROJECT / "web", file_path="../../outside.txt") == 2


def test_broken_input_fails_closed():
    assert run("Bash", raw="not json") == 2
