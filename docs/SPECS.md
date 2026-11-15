# Technical specs

Facts about the hardware and the targets that the code has to respect. Fill in or delete each `<!-- -->` line.

## Hardware

- **Board:** Raspberry Pi Zero 2 W, 512 MB RAM (~416 MB usable), Raspberry Pi OS Lite on Debian 13 (trixie), Python 3.13, picamera2 0.3.39 (as of 2026-11-14; `scripts/dev.sh --health` shows the current state)
- **Still capture memory:** the still configuration needs `buffer_count=2`; found on the device. Reason unconfirmed; likely memory at 4056x3040 + RAW. Replace this with the real reason once known.
- **Still capture API** (tested 2026-11-14, picamera2 0.3.39): `switch_mode_and_capture_buffers` works. `switch_mode_capture_request_and_stop` fails with `ENOMEM` when saving. `switch_mode_and_capture_request` is discouraged by picamera2 itself (CMA fragmentation). A capture briefly needs ~100 MB and pushes the Pi into swap; with the DNG saved first and freed before the JPEG encode, 3/3 shots ran without libcamera errors. One earlier shot without that ordering stalled the preview ("Camera frontend has timed out"). Fetch order (2026-11-15): `["raw", "main"]` failed with `ENOMEM` once at 12 MP; `["main", "raw"]` then ran 3/3. Cause unconfirmed, so keep `["main", "raw"]`.
- **Shot timing** (measured 2026-11-14, auto settings): preview back 1.6–2.4 s after the trigger, JPG + DNG saved 3.1–8.1 s after it. 3 MP (2028x1520) JPG + DNG: saved ≤ 2 s after the trigger (1 shot, 2026-11-15).
- **Capture modes** (IMX477, full field of view): 4056x3040 and 2028x1520 (2x2 binned). 2028x1080 and 1332x990 are crops, so they are not offered. JPG-only and RAW-only shots fetch only that buffer.
- **Sensor:** Raspberry Pi HQ Camera (IMX477), 4056x3040
- **Lens:** Pentax 8.5mm 1:1.5 TV Lens
- **Display:** Waveshare 3.5 inch LCD HDMI 480x320px
- **Touch controller:** XPT2046, kernel driver `ADS7846 Touchscreen` (`/dev/input/event2`): `ABS_X` 280–3840, `ABS_Y` 428–3770, `BTN_TOUCH`, no multi-touch. Raw axes vs. the screen as seen: not yet calibrated (`TOUCH_*` in `settings.py`).
- **Framebuffer:** 800x480 (`fbset`), scaled by the panel to 480x320; HUD and menu coordinates are in 800x480.
- **Shutter button:** GPIO 17 (BCM) <!-- wiring: to GND, internal pull-up? -->
- **Power:** Aim is to run off 2 x 18650 cells
- **Storage:** micro SD shared with OS 32GB
- **Enclosure / mounting:** camera sensor upright (saved photos need no rotation); display mounted upside down → `PREVIEW_ROTATE = True` rotates preview and HUD only <!-- enclosure details -->

## Targets

- **Shot-to-shot time:** 1s
- **Boot to ready:** 10s
- **Web clients at once:** 1
- **Network:** home wifi or hotspot during dev. Pi as accespoint in the future
