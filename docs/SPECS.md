# Technical specs

Facts about the hardware and the targets that the code has to respect. Fill in or delete each `<!-- -->` line.

## Hardware

- **Board:** Raspberry Pi Zero 2 W, 512 MB RAM, Raspberry Pi OS Lite
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
