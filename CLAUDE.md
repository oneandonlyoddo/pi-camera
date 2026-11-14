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
scripts/dev.sh --clean    # list files on the Pi not in the working copy; deletes after y/N (never DCIM/, .git/). Without a terminal: list only
scripts/dev.sh --install  # one-time service install
```

- Config: `PI_HOST` (default `pi`), `PI_DIR` (default `workspace/pi-camera`).
- Copies `git ls-files -co --exclude-standard`, minus `.claude/`, `audits/`, `docs/`, `scripts/` and `*.psd`. Files deleted locally stay on the Pi until `--clean`.
- The service runs from the project root with `KillSignal=SIGINT` (so `cleanup()` runs) and `Restart=always`.

On the Pi: **never use pip**. Install packages with apt (`python3-picamera2 python3-gpiozero python3-numpy python3-evdev python3-pil python3-flask`, plus `python3-pytest` for tests). To run by hand, stop the service first, because the camera, display and port 5000 can have only one owner: `sudo systemctl stop pi-camera && cd ~/workspace/pi-camera && python3 main.py`.

Line endings: the Windows checkout uses CRLF, and files are copied as-is. Keep `*.sh` and `*.service` files LF (pinned in `.gitattributes`).

## Testing

- **Tests** (`tests/`, pytest) run on the Pi: `scripts/dev.sh --test`. They cover the web API, `CameraState` and settings paths, and use a temporary DCIM (R11). Known issues with a test are marked `xfail(strict=True)`: when the fix lands, the test XPASSes and fails the run until the marker is removed.
- **Lint:** ruff 0.17.5 on the desktop (`uvx --quiet ruff@0.17.5 check .`, config in `ruff.toml`, target py313, the Pi's Python). The hook runs it after every Python edit. `ruff.toml` temporarily ignores the star-import findings (Known issue 11).
- **On-device checks:** `/on-device`. Button presses, touches and what the screen shows need a person at the device.

## Gotchas

- **Paths:** Flask resolves `DCIM/` from the project root. The camera and HUD resolve `DCIM/` and `./assets/` from the **working directory**, so always start from the project root.
- **Threads:** the camera loop runs on the main thread. Flask, the touchscreen (evdev) and the gpiozero callbacks each run on their own thread. Only the web trigger goes through `CameraState`. The button and touch callbacks call `capture_photo()` directly.
- **Runtime settings** (gain, WB) live only in memory and reset to auto on restart. Static config is in `settings.py`.
- **`GPIO_CONNECTED = False`** still creates the `Button`. Only presses are ignored.
- **`hud.py`** gets `Path` only through `from settings import *`. Do not remove the "unused" `Path` from `settings.py` before the star imports are gone (ruff ignores it until then, see `ruff.toml`).
- **Hardware facts** (display orientation, `buffer_count=2`, OS and library versions, memory): `docs/SPECS.md`. Rules about them: R8.
- **Pi folder** `~/workspace/pi-camera` is an old git clone. The desktop is the source of truth; do not use git on the Pi.
- **New runtime setting:** add it in `CameraState`, apply it in `DigitalCamera.run()` (with a `_last_*` change check), and add it to `/api/settings` and `index.html`. Then update the README.

## Known issues (not yet fixed)

1. Paths depend on the working directory (see Gotchas).
2. `capture_photo()` is called from several threads, with no lock.
3. The JPG and the DNG are two separate exposures. Measured on the device (2026-11-14): one shot takes ~10 s from trigger to preview, of which the DNG exposure is ~5.5 s.
4. The preview config rebuilt after a capture drops the `PREVIEW_ROTATE` transform: from the first photo on, the live preview is upside down on the display while the HUD stays correct (confirmed on the device; raw order changes from `SRGGB12` to `SBGGR12`). The manual `switch_mode()` is redundant. The still config correctly has no transform. (The audit in `audits/` recommends adding it; that would turn saved photos upside down in this build.) `preview_config["format"] = "YUV420"` has no effect: the device runs the preview as `XBGR8888`.
5. Colour temperature → `ColourGains` is a placeholder (red and blue gains are equal).
6. The web trigger can wait up to `HUD_UPDATE_INTERVAL` (1 s).
7. `/dcim/thumbs/<path:filename>` reads and writes paths built from the URL without checking that they stay inside `DCIM/`.
8. `/api/settings` has no range check (NaN and negative values pass).
9. Photos taken in the same second overwrite each other (timestamps have 1 s resolution).
10. Thumbnail code is duplicated in `digital_camera.py` and `web/app.py`.
11. `from settings import *` in `digital_camera.py` and `hud.py` (`hud.py` only gets `Path` through it). `ruff.toml` ignores the resulting findings until this is fixed; remove those ignores then. 6 other ruff findings remain.
12. The web sliders allow gain 0.1–0.9 and colour temperature 100–1900 K, outside the R7 ranges.
