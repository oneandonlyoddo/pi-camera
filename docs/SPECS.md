# Technical specs

Facts about the hardware and the targets that the code has to respect. Fill in or delete each `<!-- -->` line.

## Hardware

- **Board:** Raspberry Pi Zero 2 W, 512 MB RAM (~416 MB usable), Raspberry Pi OS Lite on Debian 13 (trixie), Python 3.13, picamera2 0.3.39 (as of 2026-11-14; `scripts/dev.sh --health` shows the current state)
- **Still capture memory:** the still configuration needs `buffer_count=2`; found on the device. Reason unconfirmed; likely memory at 4056x3040 + RAW. Replace this with the real reason once known.
- **Still capture API** (tested 2026-11-14, picamera2 0.3.39): `switch_mode_and_capture_buffers` works. `switch_mode_capture_request_and_stop` fails with `ENOMEM` when saving. `switch_mode_and_capture_request` is discouraged by picamera2 itself (CMA fragmentation). A capture briefly needs ~100 MB and pushes the Pi into swap; with the DNG saved first and freed before the JPEG encode, 3/3 shots ran without libcamera errors. One earlier shot without that ordering stalled the preview ("Camera frontend has timed out").
- **Shot timing** (measured 2026-11-14, auto settings): preview back 1.6–2.4 s after the trigger, JPG + DNG saved 3.1–8.1 s after it.
- **Sensor:** Raspberry Pi HQ Camera (IMX477), 4056x3040
- **Lens:** <!-- model, focal length, mount -->
- **Display:** <!-- model, size, resolution, interface (DSI/HDMI/SPI) -->
- **Touch controller:** <!-- model, evdev name -->
- **Shutter button:** GPIO 17 (BCM) <!-- wiring: to GND, internal pull-up? -->
- **Power:** <!-- battery type, capacity, target runtime -->
- **Storage:** <!-- SD card size; expected photos per session -->
- **Enclosure / mounting:** camera sensor upright (saved photos need no rotation); display mounted upside down → `PREVIEW_ROTATE = True` rotates preview and HUD only <!-- enclosure details -->

## Targets

- **Shot-to-shot time:** <!-- e.g. < 2 s -->
- **Boot to ready:** <!-- e.g. < 30 s -->
- **Web clients at once:** <!-- e.g. 1–2 phones on the same Wi-Fi -->
- **Network:** <!-- home Wi-Fi / Pi as access point / offline -->
