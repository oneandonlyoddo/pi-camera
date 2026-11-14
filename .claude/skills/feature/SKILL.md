---
name: feature
description: Add or change a camera feature end to end, from checking the feature list and specs, through a short plan, implementation and tests, to on-device verification and doc updates. Use when the user asks for a new feature or behaviour change ("add exposure control", "make the gallery refresh", "add a second button"), including new runtime settings and new shutter triggers.
argument-hint: "<feature description>"
---

# Feature workflow

## 1. Check what exists

- Read `docs/FEATURES.md`.
  - Listed under **Rejected** → stop. Tell the user it was rejected and why. Continue only if they explicitly overrule it.
  - Already `done`/`wip` → say so and ask whether this is a change to it.
- Read `docs/SPECS.md` if the feature touches capture, display, GPIO, touch, timing, memory or storage.
- Read `docs/design/hud.md` / `docs/design/web.md` (and their images) if it touches the HUD or the web UI. Respect "Must stay".

## 2. Plan (short, before writing code)

State in a few lines:
- what changes for the user
- files touched
- rules involved (R1–R11), especially R2 (threads), R6 (budget), R7 (web input), R11 (photos)
- new dependency? Name the `python3-*` apt package (R1), or say none
- how it will be verified on the device, and what needs a person

If there is a real design choice (UI placement, defaults, ranges, naming), ask the user before implementing. Otherwise proceed.

Add the feature to `docs/FEATURES.md` with status `wip`.

## 3. Implement

Follow the rules in `.claude/rules/`. For the two common cases, follow the recipe:
- new runtime camera setting (gain-like, adjustable from the web) → [setting.md](setting.md)
- new shutter trigger / input device → [trigger.md](trigger.md)

Keep the change minimal. If existing code in the way breaks a rule, mention it; fix it only if it is small and needed, otherwise leave it for the refactor.

## 4. Test

- Add or extend tests in `tests/` for anything testable without the camera: web routes, validation, `CameraState`, pure helpers (filenames, ranges, config builders).
- Logic buried in `DigitalCamera` that you need to test → extract it into a function that does not need Picamera2.

## 5. Verify on the device

Run the `/on-device` skill (verify mode). Do not call the feature done without it.

## 6. Docs (R9)

- `docs/FEATURES.md`: status → `done` (or keep `wip` with a note on what is missing)
- README: settings, API, usage
- CLAUDE.md: gotchas or known issues, if any changed
- `docs/SPECS.md`: new hardware facts (pins, devices)

## 7. Report

What changed, the `/on-device` report (verified / needs a person / not verified), and any rule violations left in place.

If the user decides against the feature at any point, move it to **Rejected** in `docs/FEATURES.md` with their reason.
