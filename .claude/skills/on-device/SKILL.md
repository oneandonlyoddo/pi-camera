---
name: on-device
description: Verify a change on the Raspberry Pi (deploy, run tests, restart, take a real photo and inspect it) or check the Pi's health. Use after every code change before calling it done (rule R10), when the user asks to test/deploy/run on the Pi, or for "is the Pi OK", "health check", "why is the camera not starting".
argument-hint: "[verify|health]"
---

# On-device verification

Nothing runs on the desktop. The Pi is the only place this code can be verified. All device access goes through `scripts/dev.sh`. Use only its non-interactive modes:

| Command | Use |
|---|---|
| `scripts/dev.sh --test` | copy + pytest on the Pi |
| `scripts/dev.sh --check` | copy + restart service + log since restart |
| `scripts/dev.sh --shoot` | web-trigger a capture on the running service, wait for JPG + DNG + thumbnail, copy JPG + thumbnail to `device-out/` |
| `scripts/dev.sh --health` | service, picamera2 version, OS, memory, disk, throttling, console blanking, groups |

Never run the interactive modes (`scripts/dev.sh` without flags, `--logs`, `--fg`); they block. Never run `--install` unless the user asks. Run commands exactly as written above (no `bash` prefix), so the permission rules match.

## Mode: verify (default)

1. **Lint** the changed Python files on the desktop: `uvx --quiet ruff check <files>`. Fix findings in code you changed.
2. **Tests:** `scripts/dev.sh --test`. A test marked `xfail(strict=True)` that now passes ("XPASS") means a known issue is fixed: remove the marker, and the issue from CLAUDE.md and README (R9).
3. **Restart:** `scripts/dev.sh --check`. On FAIL, read the log it printed, fix, repeat. Do not retry unchanged code.
4. **Shoot** if the change touches capture, camera settings, the HUD, the web server, or `main.py`: `scripts/dev.sh --shoot`.
   - Check the printed JPG size against `CAPTURE_WIDTH` x `CAPTURE_HEIGHT` in `settings.py`, and that the thumbnail fits 300x225.
   - Look at `device-out/<name>.jpg` with the Read tool: not black or blown out, upright (saved photos are never rotated; `PREVIEW_ROTATE` is for the display only), no HUD burned into the photo (the HUD is a preview overlay only).
5. **Settings changes** (gain, white balance, new runtime settings): set the value, shoot, compare with an auto shot, then reset to auto. Setting a value needs plain ssh, which asks the user for permission:
   ```bash
   ssh "${PI_HOST:-pi}" "curl -fsS -X POST -H 'Content-Type: application/json' -d '{\"gain\": 8}' localhost:5000/api/settings"
   ```
   Reset with `{"gain": 0, "color_temp": 0}` afterwards.
6. **Report** in this form:
   ```
   Verified on device: <what ran, with result: tests N passed / check OK / shot IMG_x 4056x3040 + DNG>
   Needs a person:     <button press, touch, how the preview/HUD looks on the screen, anything physical>
   Not verified:       <anything skipped and why>
   ```
   The preview on the display cannot be seen from here. Anything about what the screen shows goes under "Needs a person".

## Mode: health

Run `scripts/dev.sh --health` and interpret:

- **service** not `enabled`/`active` → the service is not installed or crashed; check the log line under "camera this boot". If not installed, tell the user to run `scripts/dev.sh --install`.
- **picamera2** version → state it when a change relies on Picamera2 API names (R8).
- **throttled** not `0x0` → under-voltage or throttling. Usually the power supply; it affects capture reliability. Tell the user.
- **consoleblank** not `0` → the console may blank the screen after a few minutes. Suggest adding `consoleblank=0` to `/boot/firmware/cmdline.txt` (user does it; it needs a reboot).
- **disk** under ~1 GB free → warn; every shot is a JPG plus a DNG of tens of MB. Check the real size with `ls -l` after a `--shoot`.
- **memory**: available under ~100 MB with the service running → warn (R6).
- **groups** missing `video`, `gpio` or `input` → camera, button or touchscreen will fail.

## When the Pi is unreachable

If ssh fails (timeout, host not found, auth), stop. Tell the user the Pi is unreachable and that the change is **not verified**. Do not fall back to desktop-only checks as a substitute.

## Rules

- Never touch photos in `DCIM/` on the Pi (R11). `device-out/` is local scratch and can be cleared.
- `PI_HOST` / `PI_DIR` come from the environment (defaults `pi`, `workspace/pi-camera`).
