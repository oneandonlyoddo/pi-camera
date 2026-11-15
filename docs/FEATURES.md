# Features

Status: `done` · `wip` · `planned` · `idea` · `rejected`. A rejected feature keeps its reason, so it isn't proposed again.

| Feature | Status | Notes |
|---|---|---|
| JPG + DNG capture at 4056x3040 | done | now one choice in the touch menu |
| Fullscreen DRM preview with HUD | done | |
| Shutter: GPIO button | done | off by default (`GPIO_CONNECTED`). 2026-11-15: 20 ms debounce, GPIO failure no longer crashes the app, mock-pin tests. Real press not yet tested on hardware |
| Shutter: touchscreen | done | any touch outside the MENU button fires |
| Shutter: web button | done | |
| Web gallery with thumbnails + lightbox | done | redesign 2026-11-15 (docs/design/web.md): orange/black palette, photos grouped by date, pill tab bar. Look still needs a person |
| Gain / white balance from web | done | gain 1–16x, WB 2000–8000 K via libcamera `ColourTemperature`; 0 = auto |
| On-screen touch menu: capture resolution + format | wip | MENU button bottom right; 12MP/3MP, JPG / RAW / JPG+RAW. Capture verified on device; touch calibrated (2026-11-15). HUD redesign: look still needs a person. DNG-only shots don't show in the web gallery (accepted) |
| Runtime settings survive restart | done | gain, WB, resolution, format in `camera_settings.json` |
| Web gallery refresh button | done | round button next to the headline reloads the photo list (no-store fetch for the iOS home-screen app). Tap still needs a person |
| EXIF in JPG + DNG | done | only values measured at capture or reported by the sensor; no aperture/lens (manual lens, unknown). Artist/Copyright from `settings.py`. Time zone, exposure/WB mode, pixel size: JPG only (pidng lacks the tags) |
| Presets / film simulation (Fuji-style recipes) | wip | 2026-11-15: verified on device (live switch, shots: Acros mono, Portra warmer R/B 1.41→1.56). Menu row taps + HUD name still need a person; step sizes still need tuning by eye. `presets.json`; colour, mono, highlight, shadow, sharpness, fixed WB (K) + WB shift, exposure comp. Applied to preview + JPG, not DNG. Switching reopens the camera with a modified tuning file. Not yet: grain, halation, colour matrix (film colour, Acros+R/G), Colour Chrome, clarity, NR. Reference recipes + sample shots: `docs/presets/` |
| White balance presets | wip | AUTO / INDOOR 3000K / FLUOR 4000K / SUNNY 5500K / CLOUDY 6500K / SHADE 7500K: fixed Kelvin shortcuts for the colour temperature (not libcamera's range-limited `AwbMode`). Touch menu row, web buttons, preset `wb` by name. 2026-11-15: menu render, web page and API checked on device; taps and how the web buttons look need a person |
| <!-- next feature --> | | |

## Rejected

- <!-- Feature: why not -->
