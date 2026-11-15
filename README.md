# Raspberry Pi Zero Digital Camera

A digital camera built on the Raspberry Pi HQ Camera module, with a built-in web interface. It turns a Raspberry Pi into a camera with a hardware shutter button, touchscreen trigger, fullscreen preview with HUD, a remote web gallery and remote controls, and saves shots as JPG, RAW (DNG) or both, chosen in an on-screen touch menu.

## Architecture

The application runs several threads:
- **Main thread**: camera preview, HUD updates, settings application and the capture loop
- **Web thread** (daemon): Flask web server for the gallery and remote control
- **Touchscreen thread** (daemon, Pi only, optional): listens for touch events via evdev
- **GPIO callback thread** (Pi only, managed by gpiozero): handles the shutter button

The web server and the camera loop communicate through a lock-protected `CameraState` object (`shared_state.py`). When you start the application, the camera preview (on the Pi's display) and the web server (at `http://<pi-ip>:5000`) run at the same time.

## Features

### Camera
- 📸 **Hardware shutter button** via GPIO (enable with `GPIO_CONNECTED = True`)
- 👆 **Touchscreen trigger**: touch anywhere outside the MENU button to capture (optional, Pi only)
- 📋 **Touch menu**: MENU button (bottom right) opens a settings list (resolution, format, preset, white balance, gain); tap a setting for its options, drag to scroll
- ☀️ **White balance presets**: AUTO, INDOOR 3000K, FLUOR 4000K, SUNNY 5500K, CLOUDY 6500K, SHADE 7500K (fixed Kelvin, `WB_PRESETS` in `settings.py`); in the touch menu and the web Settings tab
- 🎨 **Presets / film simulation**: Fuji-style recipes from `presets.json`, applied to the live preview and the JPG (see [Presets](#presets))
- 🖥️ **Fullscreen preview** on the connected display (DRM preview, 800x480)
- 📷 **Capture resolution**: 4056x3040 (12 MP) or 2028x1520 (3 MP), both the full field of view
- 🎞️ **Capture format**: JPG, RAW (DNG) or JPG + RAW (same frame)
- 💾 **Settings survive a restart**: gain, white balance, resolution, format and preset are saved to `camera_settings.json`
- 🖼️ **Thumbnails** generated on first view in the gallery (`DCIM/thumbs/`)
- 🕒 **Timestamped filenames**
- 🏷️ **EXIF in JPG and DNG**: capture time, exposure, ISO, exposure/white-balance mode, sensor model, optional artist/copyright
- 📊 **HUD overlay** with time, date, exposure, gain, white balance, capture resolution and format, and the preset name (top centre)

### Web interface
- 🖼️ **Gallery**: thumbnail grid with lazy loading, full-size lightbox on tap
- 🎮 **Remote shutter**
- ⚙️ **Live controls** for analogue gain and colour temperature
- 📱 **Mobile-friendly** layout

### Development
- 🔁 **One-command deploy**: edit on your desktop, run on the Pi with `scripts/dev.sh`

## Hardware Requirements

- Raspberry Pi (designed for Pi Zero 2 W; Pi 3/4/5 should work)
- Raspberry Pi HQ Camera module
- Push button for the shutter (optional)
- Display (HDMI or DSI) for the preview; touchscreen optional
- MicroSD card with Raspberry Pi OS

## Wiring

Connect a push button to your Raspberry Pi:
- **Button pin 1** → GPIO 17 (BCM numbering, physical pin 11)
- **Button pin 2** → GND (any ground pin)

The button uses the internal pull-up resistor, so no external resistor is needed.

**Note:** the button only triggers captures when `GPIO_CONNECTED = True` in `settings.py` (default `False`).

## Installation

### 1. Get the code

```bash
git clone https://github.com/oneandonlyoddo/pi-camera.git
cd pi-camera
```

### 2. Install dependencies

The app runs on the Raspberry Pi only. Use `apt`, not `pip`. These packages are managed by the system:

```bash
sudo apt install python3-picamera2 python3-gpiozero python3-numpy python3-evdev
sudo apt install python3-pil python3-flask
sudo apt install python3-pytest   # only needed to run the tests
```

To develop on a desktop and run on the Pi, see [Development Workflow](#development-workflow).

## Usage

### Run the camera

```bash
cd pi-camera
python3 main.py
```

To start the camera automatically at boot, install it as a systemd service (see [Development Workflow](#development-workflow)).

### Taking photos

1. The camera starts with a fullscreen preview.
2. Capture a photo with any of these:
   - **Hardware button** (if `GPIO_CONNECTED = True`)
   - **Touchscreen**: touch anywhere except the MENU button (if a touchscreen is detected)
   - **Web interface**: shutter button in the Settings tab
3. Each capture takes one exposure and saves it in the chosen format (both files from the same frame):
   - `DCIM/IMG_YYYYMMDD_HHMMSS_ffffff.jpg`: JPEG image (formats JPG and JPG+RAW)
   - `DCIM/IMG_YYYYMMDD_HHMMSS_ffffff.dng`: RAW DNG file (formats RAW and JPG+RAW)

   Both carry EXIF with only what the camera measures at capture or the sensor reports:

   | Tag | JPG | DNG |
   |---|---|---|
   | Make (`Raspberry Pi`), Model (sensor, `imx477`), Orientation | ✓ | ✓ |
   | DateTime / DateTimeOriginal, SubSecTimeOriginal (same time as the filename) | ✓ | ✓ |
   | OffsetTimeOriginal (Pi time zone) | ✓ | – |
   | ExposureTime (exact, µs) | ✓ | ✓ |
   | ISO (= total gain × 100, picamera2's convention, not a calibrated ISO) | ✓ | ✓ |
   | ExposureProgram (auto / manual gain) | ✓ | ✓ |
   | ExposureMode, WhiteBalance (auto / manual), PixelX/YDimension, ColorSpace (sRGB) | ✓ | – |
   | Artist, Copyright (if set in `settings.py`) | ✓ | ✓ |
   | Software | `pi-camera` | `PiDNG` |

   No aperture or lens tags: the manual lens can't report its aperture. "–": pidng has no such tag. The DNG also keeps pidng's colour data (CFA pattern, black/white level, colour matrix, as-shot neutral).

   The preview returns about 2 s after the trigger; the files are written a few seconds later (12 MP JPG+RAW: 5–9 s; 3 MP: about 2 s). Shutter presses during a capture are ignored. The gallery creates a 300x225 thumbnail in `DCIM/thumbs/` the first time it shows a photo.

### Touch menu

Tap **MENU** (bottom right) to open the settings list. Each row shows a setting and its current value (orange); tap it to open its options. Tap an option to select it (orange = selected) and return to the list, or **< BACK** to return without a change. **DONE** (top right of the list) closes the menu. Drag a list up or down to scroll it (a grey bar on the right shows a list is longer than the screen); a touch that moves less than 16 px counts as a tap. While the menu is open, touches never fire the shutter.

- **Resolution:** 12MP 4056x3040 (default) or 3MP 2028x1520
- **Format:** JPG, RAW (DNG only) or JPG+RAW (default)
- **Preset:** NONE (default) or a recipe from `presets.json`
- **White balance:** AUTO (default) or a WB preset; a web slider value shows as e.g. 4200K
- **Gain:** AUTO (default), 1x, 2x, 4x, 8x, 16x (`GAIN_STEPS`); a web slider value shows as e.g. 3.2x

The current resolution and format are shown top left. DNG-only shots are not listed in the web gallery.

### Using the web interface

1. **Find your Pi's IP address:**
   ```bash
   hostname -I
   ```

2. **Open** `http://<pi-ip-address>:5000` in a browser on the same network (for example `http://192.168.1.100:5000`).

3. **Gallery tab**
   - Shows all `.jpg` files in `DCIM/`, newest first (by file modification time)
   - Tap a thumbnail to open the full image
   - DNG files are not shown
   - The list loads once per page load; reload the page to see new photos

4. **Settings tab**
   - **Shutter button**: capture remotely
   - Every touch-menu setting, in the same order, one block per setting: **Resolution**, **Format**, **Preset** (option buttons), **White Balance** (slider 0 = auto up to 8000 K, step 100, plus the WB preset buttons), **Gain** (slider 0 = auto up to 16x, step 0.1, plus the gain step buttons). Orange = current value

Gain, colour temperature, resolution, format and preset are saved to `camera_settings.json` in the project folder whenever they change, and restored at startup. Delete the file to go back to the defaults (auto, 12MP, JPG+RAW, no preset). Invalid values in it are ignored with a warning in the log. `scripts/dev.sh` never copies or cleans this file.

**Security:** the web server listens on all interfaces (`0.0.0.0:5000`) with no authentication. Use it on a trusted network only.

### Exit the application

Press `Ctrl+C`. When running as a service: `sudo systemctl stop pi-camera`.

## Presets

Presets are Fuji-style film simulation recipes, defined in `presets.json` (project root) and picked in the touch menu or the web Settings tab (PRESET; NONE = off). The active preset's name shows in the top centre of the HUD. They change the live preview and the JPG; the DNG stays untouched.

```json
{"Portra": {"color": 2, "highlight": -1, "shadow": -1, "sharpness": -2, "wb_red": 2, "wb_blue": -4}}
```

| Key | Range | Does |
|---|---|---|
| `color` | -4..4 | saturation, 0.1 per step |
| `mono` | true/false | black and white (overrides `color`) |
| `highlight` / `shadow` | -4..4 | tone curve: + brightens highlights / darkens shadows |
| `sharpness` | -4..4 | 0.25 per step |
| `wb` | 2000..8000 or a name | fixed white balance in Kelvin, or a WB preset name (`"sunny"`, `"cloudy"`, ... case-insensitive); missing = auto. A manual WB from the web page overrides it |
| `wb_red` / `wb_blue` | -9..9 | shift on top of auto WB or the preset's `wb`, 5% gain per step (not on top of a web manual WB) |
| `exposure` | -3..3 | exposure compensation in EV; only with auto gain |

Missing keys are neutral. Names are at most 12 characters; invalid presets are skipped with a warning in the log. The step sizes are guesses, set in `settings.py` (`PRESET_*_STEP`); tune them by eye against the sample shots in `docs/presets/`. Highlight, shadow and WB shift live in the camera's tuning file, so switching a preset reopens the camera (~1.6 s, the preview freezes meanwhile). Not supported yet: film colour (Classic Chrome's palette), Acros+R/G filters, grain, Colour Chrome, clarity, noise reduction, dynamic range.

## Configuration

All static settings are in `settings.py`. Gain, colour temperature, resolution, format and preset are runtime settings (web interface / touch menu), saved in `camera_settings.json`; `settings.py` only defines their ranges and choices.

### GPIO
```python
GPIO_BUTTON_PIN = 17              # Shutter button pin (BCM numbering)
GPIO_DEBOUNCE_TIME = 0.02         # Contact must be stable this long (s); longer drops quick taps
GPIO_CONNECTED = False            # Set to True once the button is wired up
```

### Touchscreen
```python
TOUCHSCREEN_ENABLED = True        # Touchscreen shutter + menu (Pi only, requires evdev)
TOUCH_SWAP_XY = False             # Calibration: map touch axes onto the screen as seen
TOUCH_INVERT_X = False
TOUCH_INVERT_Y = False
TOUCH_LIFT_GRACE = 0.15          # s; shorter lifts are contact lost mid-drag, not a release
```

Every tap is logged as `Touch raw=(…) screen=(x, y)` with x, y from 0 to 1 (0, 0 = top left as you see the screen). To calibrate, follow the log (`scripts/dev.sh --logs`) and tap the corners: if x and y are swapped, set `TOUCH_SWAP_XY`; if one runs the wrong way, set its `TOUCH_INVERT_*`.

### File paths and naming
```python
PROJECT_ROOT = Path(__file__).resolve().parent   # all paths are absolute, from here
PHOTOS_DIR = PROJECT_ROOT / "DCIM"               # Photo folder
THUMBNAILS_DIR = PHOTOS_DIR / "thumbs"           # Thumbnail folder
FILENAME_PREFIX = "IMG"
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S_%f"   # microseconds: two shots never share a name
JPG_EXTENSION = ".jpg"
RAW_EXTENSION = ".dng"
SETTINGS_FILE = PROJECT_ROOT / "camera_settings.json"   # saved runtime settings
EXIF_ARTIST = ""                  # Artist tag in every photo; empty = not written
EXIF_COPYRIGHT = ""               # e.g. "(c) 2026 Your Name"; ASCII only, other characters become "?"
```

### Thumbnails
```python
THUMBNAIL_WIDTH = 300
THUMBNAIL_HEIGHT = 225
THUMBNAIL_QUALITY = 85            # JPEG quality (1-100)
```

### Resolution
```python
PREVIEW_WIDTH = 800               # Live preview
PREVIEW_HEIGHT = 480
CAPTURE_RESOLUTIONS = ((4056, 3040), (2028, 1520))   # Touch menu choices; first = default
CAPTURE_FORMATS = ("JPG", "RAW", "JPG+RAW")
CAPTURE_FORMAT_DEFAULT = "JPG+RAW"
PREVIEW_WINDOW_X = 0              # Preview window position
PREVIEW_WINDOW_Y = 0
```

### Preview
```python
PREVIEW_ROTATE = True             # Rotate preview and HUD by 180 degrees (for an upside-down display)
```

`PREVIEW_ROTATE` only affects what is shown on the display. Saved photos are never rotated.

### Timing
```python
HUD_UPDATE_INTERVAL = 1.0         # HUD refresh interval; a shutter request or setting change wakes the loop immediately
```

### Runtime setting ranges
```python
GAIN_MIN = 1.0                    # Analogue gain (0 = auto, else GAIN_MIN..GAIN_MAX)
GAIN_MAX = 16.0
COLOUR_TEMP_MIN = 2000            # Colour temperature in K (0 = auto, else MIN..MAX)
COLOUR_TEMP_MAX = 8000
```

The web API rejects values outside these ranges, and the web sliders use them.

### HUD
```python
HUD_FONT_PATH = PROJECT_ROOT / "assets" / "fonts" / "JetBrainsMono-Medium.ttf"
HUD_FONT_SIZE = 24
HUD_TIME_FORMAT = "%H:%M - %d/%m/%Y"
HUD_PADDING_W = 6                        # Left/right text padding
HUD_COLOR_ACCENT = (0xFF, 0x4D, 0x00)    # MENU button, selected option
HUD_COLOR_DARK = (0x11, 0x11, 0x11)      # Top/bottom bars, menu background, text on accent
HUD_COLOR_LIGHT = (0xF2, 0xF2, 0xF2)     # Data fields, grid, menu text
HUD_COLOR_GREY = (0x8E, 0x8E, 0x8E)      # Menu labels, unselected outline
HUD_GRID_WIDTH = 2                       # Rule-of-thirds grid, drawn in code
HUD_BAR_HEIGHT = 52                      # Top and bottom bars
```

The HUD uses only the four colours of `docs/design/colour_scheme.jpg`, solid (no transparency). Layout: a dark bar at the top (resolution + format left, time right) and at the bottom (exposure/gain/WB left, MENU right); the grid runs behind the bars.

## Development Workflow

Edit on your desktop, run on the Pi. `scripts/dev.sh` (bash; Git Bash on Windows) copies your working copy to the Pi over SSH, uncommitted changes included, and runs it there. No git push/pull in the loop.

### One-time setup

1. SSH key login to the Pi, with a host alias in `~/.ssh/config` (default alias: `pi`)
2. Passwordless `sudo` for your Pi user (default on Raspberry Pi OS)
3. Install the service:
   ```bash
   scripts/dev.sh --install
   ```

Override the defaults with environment variables: `PI_HOST` (SSH host/alias, default `pi`) and `PI_DIR` (path relative to the Pi user's home, default `workspace/pi-camera`).

### Commands

| Command | What it does |
|---|---|
| `scripts/dev.sh` | Copy, restart the service, follow the log. Ctrl+C stops following; the camera keeps running. |
| `scripts/dev.sh --fg` | Copy, stop the service, run in your terminal. Ctrl+C stops the camera; the service restarts afterwards. |
| `scripts/dev.sh --check` | Copy, restart, wait up to 20 s for the camera to initialize, print the log since restart. Exits 1 if the service is not running, the camera did not initialize, or the log contains errors. |
| `scripts/dev.sh --logs` | Follow the log only. |
| `scripts/dev.sh --clean` | List files on the Pi that are not in your working copy (e.g. deleted locally) and delete them after a y/N prompt. Never touches `DCIM/`, `.git/` or `camera_settings.json`. |
| `scripts/dev.sh --test` | Copy, run the test suite (`tests/`) on the Pi. |
| `scripts/dev.sh --shoot` | Take a photo via the web trigger, wait for JPG + DNG + thumbnail, copy JPG and thumbnail to `device-out/`. Exits 1 if a file is missing or the log has errors. |
| `scripts/dev.sh --health` | Print service state, picamera2 version, OS, memory, disk, throttling, console blanking and groups. |
| `scripts/dev.sh --install` | Install and enable the systemd service (`deploy/pi-camera.service`). |

**Notes:**
- Only files known to git are copied: tracked files plus new files that are not git-ignored. `DCIM/`, `.claude/`, `audits/`, `docs/`, `scripts/` and `.psd` files are not copied.
- Files you delete locally are not deleted on the Pi.
- The service starts at boot, restarts after a crash, and stops cleanly (`SIGINT`, same as Ctrl+C).

## Troubleshooting

### Camera not detected

```bash
rpicam-hello --list-cameras     # Raspberry Pi OS Bookworm and newer
libcamera-hello --list-cameras  # older releases
```

If the camera is not listed, check the ribbon cable and the camera configuration in `raspi-config` / `/boot/firmware/config.txt`.

### GPIO permission errors

Add your user to the `gpio` group, then log out and back in:

```bash
sudo usermod -a -G gpio $USER
```

As a last resort, run with `sudo python3 main.py`.

### Preview not showing

Make sure a display is connected via HDMI or DSI. The preview uses DRM, so it needs a console session; it does not run inside a desktop window.

### Touchscreen not working

1. **Check evdev is installed:**
   ```bash
   sudo apt install python3-evdev
   ```

2. **List input devices:**
   ```bash
   python3 -c "from evdev import list_devices, InputDevice; [print(f'{d}: {InputDevice(d).name}') for d in list_devices()]"
   ```

3. **Check permissions:** your user may need to be in the `input` group:
   ```bash
   sudo usermod -a -G input $USER
   ```
   Then log out and back in.

4. **Disable it:** set `TOUCHSCREEN_ENABLED = False` in `settings.py` if you have no touchscreen.

## API Reference

No authentication. All endpoints are served on port 5000.

### GET /
Returns the web interface (gallery and settings).

### GET /api/photos
Returns a JSON array of `.jpg` filenames in `DCIM/`, newest first (by modification time).

```json
["IMG_20260127_123456.jpg", "IMG_20260127_120000.jpg"]
```

On error: `500` with `{"error": "<message>"}`.

### GET /dcim/&lt;filename&gt;
Serves a full-size file from `DCIM/` with a 1-year cache header.

Example: `/dcim/IMG_20260127_123456.jpg`

### GET /dcim/thumbs/&lt;filename&gt;
Serves the thumbnail for a photo, generating it first if it does not exist. 1-year cache header.

- `404` with `{"error": "Image not found"}` if the original photo does not exist, or if the name is not a plain filename (no folders, no `..`)
- `500` with `{"error": "Failed to generate thumbnail"}` if generation fails

### POST /api/trigger
Requests a capture. The camera starts it immediately; requests made while a capture is running are ignored.

```json
{"status": "ok", "message": "Shutter requested"}
```

### GET /api/settings
Returns the current runtime settings.

```json
{"gain": 0.0, "color_temp": 0, "resolution": [4056, 3040], "format": "JPG+RAW", "preset": ""}
```

### POST /api/settings
Updates any of the fields; all are optional. `gain` and `color_temp` must be `0` (automatic) or within their range in `settings.py`: gain `1.0`–`16.0`, colour temperature `2000`–`8000` K. `resolution` must be one of `CAPTURE_RESOLUTIONS` as `[width, height]`, `format` one of `CAPTURE_FORMATS`, `preset` a name in `presets.json` or `""` (none). A preset change reopens the camera (about 1.6 s).

**Request:**
```json
{"gain": 2.5, "format": "RAW"}
```

**Response:** every setting, as GET returns it
```json
{"status": "ok", "gain": 2.5, "color_temp": 0, "resolution": [4056, 3040], "format": "RAW", "preset": ""}
```

- `400` with `{"status": "error", "message": "..."}` if the body is empty or not a JSON object, or any value is invalid (out of range, not a number, NaN, `true`/`false`). Nothing is changed then, not even a valid value in the same request.

## Known Issues

- **The HUD pauses while a photo is saved:** writing the JPG and DNG takes a few seconds on the Pi Zero, during which the HUD is not updated and shutter presses are ignored. The preview itself keeps running.

## File Structure

```
pi-camera/
├── main.py              # Entry point: starts Flask thread, runs camera loop
├── digital_camera.py    # Camera controller (Picamera2, GPIO, touchscreen)
├── touchscreen.py       # Touchscreen input via evdev (Pi only)
├── shared_state.py      # Thread-safe state shared between web server and camera
├── hud.py               # HUD overlay (PIL)
├── menu.py              # Touch menu layout, tap and drag handling
├── exif.py              # EXIF tags for JPG (piexif) and DNG (pidng)
├── settings.py          # Static configuration
├── web/
│   ├── app.py           # Flask app and API routes
│   ├── static/
│   │   └── styles.css   # Web interface styles
│   └── templates/
│       └── index.html   # Gallery and settings UI
├── assets/
│   └── fonts/           # HUD font (JetBrains Mono, OFL)
├── scripts/
│   └── dev.sh           # Desktop → Pi deploy, run and log commands
├── deploy/
│   └── pi-camera.service  # systemd unit template
├── tests/               # pytest suite, runs on the Pi (scripts/dev.sh --test)
├── docs/                # Feature list, specs, design notes
├── .claude/             # Claude Code harness: rules, skills, hooks, settings
├── DCIM/                # Photos (created automatically, git-ignored)
│   └── thumbs/          # Thumbnails
├── ruff.toml            # Lint config (desktop)
├── CLAUDE.md            # Guidance for Claude Code
└── README.md
```

## License

This project is open source and available for personal and educational use.

## Acknowledgments

Built using the [picamera2](https://github.com/raspberrypi/picamera2) library from Raspberry Pi.
