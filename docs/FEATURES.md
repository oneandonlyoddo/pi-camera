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
| Runtime settings survive restart | done | gain, WB, resolution, format, preset in `camera_settings.json` |
| Web gallery refresh button | done | round button next to the headline reloads the photo list (no-store fetch for the iOS home-screen app). Tap still needs a person |
| EXIF in JPG + DNG | done | only values measured at capture or reported by the sensor; no aperture/lens (manual lens, unknown). Artist/Copyright from `settings.py`. Time zone, exposure/WB mode, pixel size: JPG only (pidng lacks the tags) |
| Presets / film simulation (Fuji-style recipes) | wip | 2026-11-15: verified on device (live switch, shots: Acros mono, Portra warmer R/B 1.41→1.56). Menu row taps + HUD name still need a person; step sizes still need tuning by eye. `presets.json`; colour, mono, highlight, shadow, sharpness, fixed WB (K) + WB shift, exposure comp. Applied to preview + JPG, not DNG. Switching reopens the camera with a modified tuning file. Not yet: grain, halation, colour matrix (film colour, Acros+R/G), Colour Chrome, clarity, NR. Reference recipes + sample shots: `docs/presets/` |
| White balance presets | wip | AUTO / INDOOR 3000K / FLUOR 4000K / SUNNY 5500K / CLOUDY 6500K / SHADE 7500K: fixed Kelvin shortcuts for the colour temperature (not libcamera's range-limited `AwbMode`). Touch menu row, web buttons, preset `wb` by name. 2026-11-15: menu render, web page and API checked on device; taps and how the web buttons look need a person |
| Nested settings menu (Pi) + all settings on the web | done | Pi: MENU → scrollable category list (current value per row) → scrollable option page with BACK; tap selects and goes back; drag to scroll. Lifts under 150 ms are merged (`TOUCH_LIFT_GRACE`): the resistive panel loses contact mid-drag. New GAIN category with steps AUTO/1/2/4/8/16x. Web: one page with a block per setting, resolution/format/preset/gain chips added; `/api/settings` takes `resolution`/`format`/`preset`. 2026-11-15: verified on device (tests, API, 12MP JPG+DNG shot); taps, drags and the web page confirmed by the user on the Pi and phone |
| Desktop web dev server with dummy photos | done | `uv run scripts/web_dev.py` (2026-11-20): real Flask app, in-memory state, 30 generated JPGs over several days in `dev-photos/`, or `--photos device-out`. Dev tool only; never copied to the Pi |
| <!-- next feature --> | | |

## Rejected

- <!-- Feature: why not -->
