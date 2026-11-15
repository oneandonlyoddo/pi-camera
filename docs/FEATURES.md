# Features

Status: `done` · `wip` · `planned` · `idea` · `rejected`. A rejected feature keeps its reason, so it isn't proposed again.

| Feature | Status | Notes |
|---|---|---|
| JPG + DNG capture at 4056x3040 | done | now one choice in the touch menu |
| Fullscreen DRM preview with HUD | done | |
| Shutter: GPIO button | done | off by default (`GPIO_CONNECTED`) |
| Shutter: touchscreen | done | any touch outside the MENU button fires |
| Shutter: web button | done | |
| Web gallery with thumbnails + lightbox | done | |
| Gain / white balance from web | done | gain 1–16x, WB 2000–8000 K via libcamera `ColourTemperature`; 0 = auto |
| On-screen touch menu: capture resolution + format | wip | MENU button bottom right; 12MP/3MP, JPG / RAW / JPG+RAW. Capture verified on device; touch calibrated (2026-11-15). HUD redesign: look still needs a person. DNG-only shots don't show in the web gallery (accepted) |
| Runtime settings survive restart | done | gain, WB, resolution, format in `camera_settings.json` |
| <!-- next feature --> | | |

## Rejected

- <!-- Feature: why not -->
