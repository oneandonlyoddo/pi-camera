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
- 📋 **Touch menu**: MENU button (bottom right) to choose capture resolution and format
- 🖥️ **Fullscreen preview** on the connected display (DRM preview, 800x480)
- 📷 **Capture resolution**: 4056x3040 (12 MP) or 2028x1520 (3 MP), both the full field of view
- 🎞️ **Capture format**: JPG, RAW (DNG) or JPG + RAW (same frame)
- 💾 **Settings survive a restart**: gain, white balance, resolution and format are saved to `camera_settings.json`
- 🖼️ **Thumbnails** generated on first view in the gallery (`DCIM/thumbs/`)
- 🕒 **Timestamped filenames**
- 📊 **HUD overlay** with time, date, exposure, gain, white balance, capture resolution and format

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

   The preview returns about 2 s after the trigger; the files are written a few seconds later (12 MP JPG+RAW: 5–9 s; 3 MP: about 2 s). Shutter presses during a capture are ignored. The gallery creates a 300x225 thumbnail in `DCIM/thumbs/` the first time it shows a photo.

### Touch menu

Tap **MENU** (bottom right) to open the settings menu. Tap an option to select it (orange = selected), then **DONE** to close. While the menu is open, touches never fire the shutter.

- **Resolution:** 12MP 4056x3040 (default) or 3MP 2028x1520
- **Format:** JPG, RAW (DNG only) or JPG+RAW (default)

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
   - **Analogue gain**: 0 = auto, up to 16x (step 0.1)
   - **Colour temperature**: 0 = auto, up to 8000 K (step 100)

Gain, colour temperature, resolution and format are saved to `camera_settings.json` in the project folder whenever they change, and restored at startup. Delete the file to go back to the defaults (auto, 12MP, JPG+RAW). Invalid values in it are ignored with a warning in the log. `scripts/dev.sh` never copies or cleans this file.

**Security:** the web server listens on all interfaces (`0.0.0.0:5000`) with no authentication. Use it on a trusted network only.

### Exit the application

Press `Ctrl+C`. When running as a service: `sudo systemctl stop pi-camera`.

## Configuration

All static settings are in `settings.py`. Gain, colour temperature, resolution and format are runtime settings (web interface / touch menu), saved in `camera_settings.json`; `settings.py` only defines their ranges and choices.

### GPIO
```python
GPIO_BUTTON_PIN = 17              # Shutter button pin (BCM numbering)
GPIO_DEBOUNCE_TIME = 0.3          # Debounce time in seconds
GPIO_CONNECTED = False            # Set to True once the button is wired up
```

### Touchscreen
```python
TOUCHSCREEN_ENABLED = True        # Touchscreen shutter + menu (Pi only, requires evdev)
TOUCH_SWAP_XY = False             # Calibration: map touch axes onto the screen as seen
TOUCH_INVERT_X = False
TOUCH_INVERT_Y = False
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

You can also run the web server alone on the Pi, without the camera (trigger and settings return errors):
```bash
python3 web/app.py
```

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
{"gain": 0.0, "color_temp": 0}
```

### POST /api/settings
Updates `gain` and/or `color_temp`. Both fields are optional. Each must be `0` (automatic) or within its range in `settings.py`: gain `1.0`–`16.0`, colour temperature `2000`–`8000` K.

**Request:**
```json
{"gain": 2.5, "color_temp": 5000}
```

**Response:**
```json
{"status": "ok", "gain": 2.5, "color_temp": 5000}
```

- `400` with `{"status": "error", "message": "..."}` if the body is empty or any value is invalid (out of range, not a number, NaN, `true`/`false`). Nothing is changed then, not even a valid value in the same request.

`/api/trigger` and `/api/settings` return `500` if the app was started without camera state (for example `python web/app.py`).

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
├── menu.py              # Touch menu layout and tap handling
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
