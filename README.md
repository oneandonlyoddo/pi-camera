# Raspberry Pi Zero Digital Camera

A digital camera built on the Raspberry Pi HQ Camera module, with a built-in web interface. It turns a Raspberry Pi into a camera with a hardware shutter button, touchscreen trigger, fullscreen preview with HUD, a remote web gallery and remote controls, and saves every shot as JPG and RAW (DNG).

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
- 👆 **Touchscreen trigger**: touch anywhere on the screen to capture (optional, Pi only)
- 🖥️ **Fullscreen preview** on the connected display (DRM preview, 800x480)
- 📷 **Full-resolution capture**: 4056x3040 (12.3 MP)
- 🎞️ **JPG + RAW (DNG)** for every shot
- 🖼️ **Thumbnails** generated right after capture (`DCIM/thumbs/`)
- 🕒 **Timestamped filenames**
- 📊 **HUD overlay** with time, date, exposure, gain and white balance

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

`requirements.txt` lists the same packages for reference.

To develop on a desktop and run on the Pi, see [Development Workflow](#development-workflow).

## Usage

### Run the camera

**Always start the app from the project folder.** The camera saves photos and loads HUD assets relative to the current working directory, while the web server always uses the project folder (see [Known Issues](#known-issues)).

```bash
cd pi-camera
python3 main.py
```

To start the camera automatically at boot, install it as a systemd service (see [Development Workflow](#development-workflow)).

### Taking photos

1. The camera starts with a fullscreen preview.
2. Capture a photo with any of these:
   - **Hardware button** (if `GPIO_CONNECTED = True`)
   - **Touchscreen**: touch anywhere on the screen (if a touchscreen is detected)
   - **Web interface**: shutter button in the Settings tab (may take up to ~1 s to fire)
3. Photos are saved to `DCIM/`, thumbnails to `DCIM/thumbs/`.
4. Each capture creates:
   - `IMG_YYYYMMDD_HHMMSS.jpg`: JPEG image
   - `IMG_YYYYMMDD_HHMMSS.dng`: RAW DNG file
   - `thumbs/IMG_YYYYMMDD_HHMMSS.jpg`: 300x225 thumbnail

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

Settings are kept in memory only and reset to auto when the app restarts.

**Security:** the web server listens on all interfaces (`0.0.0.0:5000`) with no authentication. Use it on a trusted network only.

### Exit the application

Press `Ctrl+C`. When running as a service: `sudo systemctl stop pi-camera`.

## Configuration

All static settings are in `settings.py`. Gain and colour temperature are runtime settings controlled from the web interface and are not in `settings.py`.

### GPIO
```python
GPIO_BUTTON_PIN = 17              # Shutter button pin (BCM numbering)
GPIO_DEBOUNCE_TIME = 0.3          # Debounce time in seconds
GPIO_CONNECTED = False            # Set to True once the button is wired up
```

### Touchscreen
```python
TOUCHSCREEN_ENABLED = True        # Touchscreen shutter (Pi only, requires evdev)
```

### File paths and naming
```python
PHOTOS_DIR = "DCIM"               # Photo folder
THUMBNAILS_DIR = "DCIM/thumbs"    # Thumbnail folder
FILENAME_PREFIX = "IMG"
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
JPG_EXTENSION = ".jpg"
RAW_EXTENSION = ".dng"
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
CAPTURE_WIDTH = 4056              # Still capture
CAPTURE_HEIGHT = 3040
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
CAPTURE_PAUSE_DURATION = 0.5      # Pause after capture before returning to preview
HUD_UPDATE_INTERVAL = 1.0         # Camera loop interval (HUD refresh, web trigger polling)
```

### HUD
```python
HUD_FONT_PATH = "./assets/fonts/JetBrainsMono-Medium.ttf"
HUD_FONT_SIZE = 24
HUD_TIME_FORMAT = "%H:%M - %d/%m/%Y"
HUD_PADDING_W = 6
HUD_PADDING_H = 6
HUD_COLOR_WHITE = (255, 255, 255, 255)   # Time/date text (RGBA)
HUD_COLOR_BLACK = (0, 0, 0, 255)         # Exposure/gain/WB text (RGBA)
HUD_BACKGROUND_IMAGE_PATH = "./assets/hud_grid.png"  # Set to None for a transparent background
```

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
| `scripts/dev.sh --clean` | List files on the Pi that are not in your working copy (e.g. deleted locally) and delete them after a y/N prompt. Never touches `DCIM/` or `.git/`. |
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

### Photos missing from the gallery

Make sure you started `main.py` from the project folder. Otherwise the camera saves to a `DCIM/` folder under your current directory, while the gallery reads from the project's `DCIM/`.

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

- `404` with `{"error": "Image not found"}` if the original photo does not exist
- `500` with `{"error": "Failed to generate thumbnail"}` if generation fails

### POST /api/trigger
Requests a capture. The camera loop picks the request up on its next iteration (up to `HUD_UPDATE_INTERVAL`, 1 s by default).

```json
{"status": "ok", "message": "Shutter requested"}
```

### GET /api/settings
Returns the current runtime settings.

```json
{"gain": 0.0, "color_temp": 0}
```

### POST /api/settings
Updates `gain` (float) and/or `color_temp` (int). Both fields are optional. `0` means automatic.

**Request:**
```json
{"gain": 2.5, "color_temp": 5000}
```

**Response:**
```json
{"status": "ok", "gain": 2.5, "color_temp": 5000}
```

- `400` if the body is empty
- Values that cannot be converted are silently ignored
- Values are not range-checked

`/api/trigger` and `/api/settings` return `500` if the app was started without camera state (for example `python web/app.py`).

## Known Issues

- **Paths depend on the working directory:** the camera classes and the HUD use paths from `settings.py` relative to the current directory; the web server resolves them from the project folder. Start the app from the project folder.
- **JPG and DNG are separate exposures:** they are captured with two consecutive capture calls, so they are not the same frame. One shot takes about 10 s.
- **Preview flips after the first photo:** with `PREVIEW_ROTATE = True`, the live preview is upside down from the first capture on (the HUD stays correct), because the preview configuration rebuilt after capture does not reapply the rotation.
- **Colour temperature is approximate:** manual white balance sets red and blue gains to the same value (`temp / 4000`), which is not a real colour-temperature mapping.
- **Concurrent triggers:** the GPIO button and touchscreen call the capture directly from their own threads, which can collide with the camera loop or with each other.
- **Same-second captures overwrite each other:** filenames only have 1-second resolution.
- **Thumbnail route does not validate filenames:** `/dcim/thumbs/<filename>` does not check that the path stays inside `DCIM/`.

## File Structure

```
pi-camera/
├── main.py              # Entry point: starts Flask thread, runs camera loop
├── digital_camera.py    # Camera controller (Picamera2, GPIO, touchscreen)
├── touchscreen.py       # Touchscreen input via evdev (Pi only)
├── shared_state.py      # Thread-safe state shared between web server and camera
├── hud.py               # HUD overlay (PIL)
├── settings.py          # Static configuration
├── web/
│   ├── app.py           # Flask app and API routes
│   ├── static/
│   │   └── styles.css   # Web interface styles
│   └── templates/
│       └── index.html   # Gallery and settings UI
├── assets/
│   ├── fonts/           # HUD font (JetBrains Mono, OFL)
│   ├── hud_grid.png     # HUD background
│   └── hud_grid.psd     # HUD background source
├── scripts/
│   └── dev.sh           # Desktop → Pi deploy, run and log commands
├── deploy/
│   └── pi-camera.service  # systemd unit template
├── tests/               # pytest suite, runs on the Pi (scripts/dev.sh --test)
├── docs/                # Feature list, specs, design notes
├── .claude/             # Claude Code harness: rules, skills, hooks, settings
├── DCIM/                # Photos (created automatically, git-ignored)
│   └── thumbs/          # Thumbnails
├── requirements.txt     # Python dependencies (reference; install via apt)
├── ruff.toml            # Lint config (desktop)
├── CLAUDE.md            # Guidance for Claude Code
└── README.md
```

## License

This project is open source and available for personal and educational use.

## Acknowledgments

Built using the [picamera2](https://github.com/raspberrypi/picamera2) library from Raspberry Pi.
