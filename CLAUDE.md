# CLAUDE.md

## Vision

<!-- 3–5 lines: what this camera is for, who uses it, what "done" looks like. -->

A Raspberry Pi Zero 2 W camera with the HQ Camera: fullscreen preview with a HUD, JPG + DNG capture, and a web page for the gallery and remote control.

**Constraints:** 512 MB RAM and a slow CPU. Raspberry Pi OS Lite with no desktop, and the preview runs over DRM. The app runs only on the Pi. One user on the local network, and the web server has no authentication.

## Project context (read when relevant)

- [docs/FEATURES.md](docs/FEATURES.md): feature status and rejected ideas. Read it before proposing or adding a feature, and update it after.
- [docs/SPECS.md](docs/SPECS.md): hardware and performance targets. Read it before changing capture, display, GPIO, touch or performance.
- [docs/design/hud.md](docs/design/hud.md) + images: read before changing `hud.py` or the HUD assets.
- [docs/design/web.md](docs/design/web.md) + images: read before changing `web/templates/` or `web/static/`.
- `audits/`: earlier audit reports. Known Issues below is the current list.

## Harness

- **Rules** (`.claude/rules/`): `core.md` R1, R4, R6, R9, R10, R11 (always loaded); `camera.md` R2, R8 (camera files); `web.md` R7 (`web/**`). They describe the target state; the code breaks some of them (Known issues). Cite rule IDs in plans and commits.
- **Skills:** `/on-device` (verify on the Pi, health check), `/feature` (feature workflow, with recipes for settings and triggers), `/sync-docs` (docs vs code).
- **Hooks:**
  - `guard.py` (before every tool call) blocks (1) anything that could delete, move or overwrite `DCIM/` (R11) and (2) file access outside the project: home folder, absolute paths elsewhere, `..` escapes. Allowed outside: the session scratchpad, Claude's own folder for this project, reading plugin files; `~` in `ssh` commands means the Pi. It fails closed (blocks on its own errors). Tests: `uvx --quiet --with pytest pytest -q -p no:cacheprovider .claude/hooks`.
  - `ruff_check.py` (after every Python edit) reports ruff findings for that file; skips quietly if ruff cannot run.
- **Permissions** (`.claude/settings.json`): non-interactive `dev.sh` modes and read-only git are allowed; plain `ssh`/`scp`, ruff by hand, and interactive `dev.sh` modes ask.

## Dev loop (Windows desktop → Pi)

Code is edited on Windows. `scripts/dev.sh` copies the working copy to the Pi over SSH (no git) and runs it as the systemd service `pi-camera`:

```bash
# non-interactive (use these)
scripts/dev.sh --check    # copy, restart, wait for camera init; exit 1 on error or no init within 20 s
scripts/dev.sh --test     # copy, pytest on the Pi
scripts/dev.sh --shoot    # web-trigger a capture, verify JPG + DNG + thumb, copy to device-out/
scripts/dev.sh --health   # service, picamera2 version, memory, disk, throttling, ...
# interactive (block; for the user)
scripts/dev.sh            # copy, restart, follow log
scripts/dev.sh --fg       # copy, stop service, run in terminal
scripts/dev.sh --logs     # follow log
scripts/dev.sh --clean    # list files on the Pi not in the working copy; deletes after y/N (never DCIM/, .git/, camera_settings.json). Without a terminal: list only
scripts/dev.sh --install  # one-time service install
```

- Config: `PI_HOST` (default `pi`), `PI_DIR` (default `workspace/pi-camera`).
- Copies `git ls-files -co --exclude-standard`, minus `.claude/`, `audits/`, `docs/`, `scripts/` and `*.psd`. Files deleted locally stay on the Pi until `--clean`.
- The service runs from the project root with `KillSignal=SIGINT` (so `cleanup()` runs) and `Restart=always`.

On the Pi: **never use pip**. Install packages with apt (`python3-picamera2 python3-gpiozero python3-numpy python3-evdev python3-pil python3-flask`, plus `python3-pytest` for tests). To run by hand, stop the service first, because the camera, display and port 5000 can have only one owner: `sudo systemctl stop pi-camera && cd ~/workspace/pi-camera && python3 main.py`.

Line endings: the Windows checkout uses CRLF, and files are copied as-is. Keep `*.sh` and `*.service` files LF (pinned in `.gitattributes`).

## Testing

- **Tests** (`tests/`, pytest) run on the Pi: `scripts/dev.sh --test`. They cover the web API, `CameraState` and settings paths, and use a temporary DCIM (R11). Known issues with a test are marked `xfail(strict=True)`: when the fix lands, the test XPASSes and fails the run until the marker is removed.
- **Lint:** ruff 0.17.5 on the desktop (`uvx --quiet ruff@0.17.5 check .`, config in `ruff.toml`, target py313, the Pi's Python). The hook runs it after every Python edit. The repo is clean (0 findings, no ignores).
- **On-device checks:** `/on-device`. Button presses, touches and what the screen shows need a person at the device.

## Gotchas

- **Paths** in `settings.py` are absolute `Path`s from `PROJECT_ROOT` (R4); the app works from any working directory.
- **Threads:** the camera loop runs on the main thread and is the only code that touches Picamera2 (R2). Flask, the touchscreen (evdev) and gpiozero callbacks run on their own threads and only write `CameraState`: `request_capture(source)` / `shutter_requested`, settings, or (touch) `menu.handle_tap()`. Every write sets one wake `threading.Event` that the loop waits on (`CameraState.wait()`), so a menu tap redraws the HUD at once.
- **Capture** (`capture_photo`): one exposure via `switch_mode_and_capture_buffers`, DNG saved first, then JPG. It runs on the camera loop, so the HUD pauses while saving (~4–6 s) and requests made meanwhile are dropped. Why this API and not the others: `docs/SPECS.md`.
- **EXIF** (`exif.py`): only values measured at capture or reported by the sensor; no aperture/lens tags (the manual lens can't report them, the user's decision). JPG: `helpers.save(..., exif_data=jpeg_exif(...))` replaces picamera2's EXIF per IFD, so `"0th"`/`"Exif"` must be complete. DNG: `DigitalCamera._save_dng()` writes through pidng directly (helpers.save_dng can't take extra tags), using the private `helpers._make_array_shared`; recheck it on a picamera2 upgrade. pidng text tags must be ASCII, and pidng adds its own `Software` tag.
- **Touch menu** (`menu.py`): one layout in HUD pixels as the user sees the screen; `hud.py` draws it and `handle_tap()` hit-tests it. Touch positions come from `touchscreen.to_screen()` with the `TOUCH_*` calibration flags in `settings.py`.
- **Thumbnails** are made only on demand by `web/app.py` (first gallery view); the camera does not make them.
- **Runtime settings** (gain, WB, capture resolution, format) are in `CameraState`; the camera loop saves them to `camera_settings.json` (git-ignored, never copied or cleaned by `dev.sh`) when they change, and `main.py` loads them at startup (invalid values skipped). To test a resolution/format on the Pi without touching the screen, write that file and restart the service. Choices: `CAPTURE_RESOLUTIONS` / `CAPTURE_FORMATS`. Ranges: `GAIN_*` / `COLOUR_TEMP_*` in `settings.py`, used by the API validation and the web sliders. `controls_for()` in `digital_camera.py` maps them to Picamera2 controls (`ColourTemperature`, not `ColourGains`).
- **Hardware facts** (display orientation, `buffer_count=2`, capture memory, OS and library versions): `docs/SPECS.md`. Rules about them: R8.
- **Pi folder** `~/workspace/pi-camera` is an old git clone. The desktop is the source of truth; do not use git on the Pi.
- **New runtime setting:** follow `.claude/skills/feature/setting.md`.

## Known issues (not yet fixed)

1. The HUD pauses and shutter requests are dropped while a photo is saved (~4–6 s on the camera loop). Measured 2026-11-14: preview back 1.6–2.4 s after the trigger, JPG + DNG saved 5.8–8.1 s after it.
2. When a capture fails, `/api/trigger` has already answered "ok"; the web page gets no feedback.
