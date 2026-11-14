# Core rules

These rules describe the target state. Where existing code breaks a rule, it is listed in CLAUDE.md "Known issues" until it is refactored. Cite rules by ID (e.g. "R4") in plans, reviews and commit messages.

## R1 · Dependencies come from apt
- The app runs only on the Pi (Raspberry Pi OS Lite). Never use pip there.
- A new dependency must exist as a `python3-*` package in Raspberry Pi OS apt. Name the package in the change and add it to the apt lines in README and CLAUDE.md, and to `requirements.txt`.
- Prefer the standard library over a new dependency.

## R4 · Paths come from the project root
- Every file path (photos, thumbnails, assets) is resolved from one `PROJECT_ROOT` defined in `settings.py` (`Path(__file__).resolve().parent`).
- No path may depend on the working directory. `Path("DCIM")`, `"./assets/..."` and `os.getcwd()` are not allowed.

## R6 · Stay inside the Pi Zero 2 W budget
- Respect the hardware and targets in `docs/SPECS.md`. If a change can affect a target there (shot-to-shot, boot time, memory), say how.
- The camera loop must not block for more than ~100 ms, except for the capture itself.
- A web request must not decode a full-resolution image, except for one-time thumbnail generation.
- No background thread or process without a stop path in `cleanup()`.

## R9 · Docs ship with the code
In the same change that alters behaviour, update:
- README (settings, API, install, usage) and CLAUDE.md (dev loop, gotchas, known issues)
- `docs/FEATURES.md` when a feature changes status
- `docs/SPECS.md` when a hardware fact or target changes

Remove a Known issue from CLAUDE.md and README when it is fixed.

## R10 · Verify on the device
- Nothing runs on the desktop. Verify every code change on the Pi with the `/on-device` skill (at minimum `scripts/dev.sh --check`; plus `--shoot` for anything touching capture, settings or the web).
- Report exactly what was verified and what still needs a person at the device (button presses, touches, how the screen looks).
- Never claim a change works on the strength of a desktop-only check (ruff, reading code).

## R11 · Photos are user data
- Never delete, move, rename or overwrite anything in `DCIM/`, locally or on the Pi. A hook blocks the obvious commands, but this rule also covers code: no code path may overwrite an existing photo.
- Tests use a temporary directory, never the real `DCIM/`.
