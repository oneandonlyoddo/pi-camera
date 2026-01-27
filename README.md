# Raspberry Pi Zero Digital Camera

A digital camera implementation using the Raspberry Pi HQ Camera module with integrated web interface. This project turns your Raspberry Pi into a fully functional digital camera with hardware button control, fullscreen preview, remote web access, and high-quality image capture in both JPG and RAW formats.

## Architecture

This application uses a multi-threaded architecture:
- **Main Thread**: Runs the camera preview and capture loop
- **Background Thread**: Runs a Flask web server for remote access
- **Shared State**: Thread-safe communication between camera and web interface

When you start the application, both the camera interface (with fullscreen preview on the Pi's display) and the web server (accessible at `http://<pi-ip>:5000`) run simultaneously. You can capture photos using either the physical button or the web interface.

## Features

### Camera Features
- 📸 **Hardware Shutter Button** - Physical button trigger via GPIO
- 👆 **Touchscreen Support** - Touch anywhere on screen to capture (optional, requires touchscreen display)
- 🖥️ **Fullscreen Preview** - Live camera preview on connected display
- 📷 **High-Resolution Capture** - Full 4056x3040 resolution (12.3 MP)
- 🎞️ **Dual Format Saving** - Captures both JPG and RAW (DNG) formats
- 🕒 **Timestamped Files** - Automatic filename generation with timestamps
- 📊 **HUD Overlay** - Real-time display of date, time, exposure, gain, and white balance

### Web Interface Features
- 🌐 **Remote Web Access** - Control camera from any device on your network
- 🖼️ **Photo Gallery** - Browse captured images in a responsive grid layout
- 🔍 **Lightbox View** - Full-screen image preview with modal viewer
- 🎮 **Remote Shutter** - Trigger camera capture from the web interface
- ⚙️ **Live Settings Control** - Adjust analogue gain and color temperature remotely
- 📱 **Mobile Friendly** - Responsive design optimized for phones and tablets

### Development Features
- 💻 **Webcam Fallback** - Development mode using standard webcams for testing without Pi hardware
- 🔄 **Thread-Safe Architecture** - Separate threads for camera and web server with shared state management

## Hardware Requirements

- Raspberry Pi (tested on Pi Zero, compatible with Pi 3/4/5)
- Raspberry Pi HQ Camera module
- Push button for shutter control
- Display (HDMI or DSI) for preview
- MicroSD card with Raspberry Pi OS

## Wiring

Connect a push button to your Raspberry Pi:
- **Button Pin 1** → GPIO 17 (BCM numbering, Physical Pin 11)
- **Button Pin 2** → GND (any ground pin)

The button uses the internal pull-up resistor, so no external resistor is needed.

## Installation

### 1. Clone or Download the Project

```bash
git clone github.com/oneandonlyoddo/pi-camera
cd pi-camera
```

Or download the files directly to your Raspberry Pi.

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt

**Note:** These dependencies are Raspberry Pi-specific and must be installed on the Pi itself. On some Raspbian distros these packages are managed and need to be intstalled via apt. 
for example:
```bash
sudo apt install python3-picamera2
```

## Usage

### Run the Camera

```bash
python main.py
```

Or make it executable and run directly:

```bash
chmod +x main.py
./main.py
```

### Taking Photos

1. The camera will start with a fullscreen preview
2. Capture a photo using any of these methods:
   - **Hardware Button**: Press the physical GPIO button
   - **Touchscreen**: Touch anywhere on the screen (if touchscreen is connected)
   - **Web Interface**: Use the shutter button in the settings tab
3. Photos are saved to `./DCIM` by default
4. Each capture creates two files:
   - `IMG_YYYYMMDD_HHMMSS.jpg` - JPEG image
   - `IMG_YYYYMMDD_HHMMSS.dng` - RAW DNG file

### Using the Web Interface

Once the camera is running, you can access the web interface from any device on the same network:

1. **Find your Pi's IP address**:
   ```bash
   hostname -I
   ```

2. **Open a web browser** and navigate to:
   ```
   http://<pi-ip-address>:5000
   ```
   For example: `http://192.168.1.100:5000`

3. **Gallery Tab**: View all captured photos in a responsive grid
   - Tap any thumbnail to view full-screen
   - Photos are sorted with newest first
   - Lazy loading for better performance

4. **Settings Tab**: Remote camera control
   - **Shutter Button**: Capture photos remotely
   - **Analogue Gain**: Adjust sensor gain (0 = Auto, up to 16x)
   - **Color Temperature**: Set white balance (0 = Auto, up to 8000K)

### Exit the Application

Press `Ctrl+C` to safely shut down the camera.

## Configuration

All configurable settings are centralized in `settings.py`. You can customize the camera behavior by editing this file.

### Key Settings Categories

#### GPIO Configuration
```python
GPIO_BUTTON_PIN = 17              # GPIO pin for shutter button (BCM numbering)
GPIO_DEBOUNCE_TIME = 0.3          # Button debounce time in seconds
GPIO_CONNECTED = False            # Set to True when hardware button is wired up
```

#### Touchscreen Configuration
```python
TOUCHSCREEN_ENABLED = True        # Enable touchscreen shutter trigger (requires evdev)
```

#### File Paths and Naming
```python
PHOTOS_DIR = "./DCIM"             # Photo save location
FILENAME_PREFIX = "IMG"           # Prefix for saved image files
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"  # Timestamp format
```

#### Camera Resolution
```python
# Preview resolution (for live view)
PREVIEW_WIDTH = 800
PREVIEW_HEIGHT = 480

# Capture resolution (for high-res still images)
CAPTURE_WIDTH = 4056
CAPTURE_HEIGHT = 3040
```

#### HUD (Heads-Up Display)
```python
HUD_FONT_SIZE = 24                           # Font size
HUD_PADDING_W = 6                            # Horizontal padding
HUD_PADDING_H = 6                            # Vertical padding
HUD_COLOR_TEXT = (0, 0, 0, 255)              # Black text (RGBA)
HUD_BACKGROUND_IMAGE_PATH = "./assets/hud_grid.png"  # Optional background image
```

#### Preview Settings
```python
PREVIEW_ROTATE = False            # Set to True to rotate preview 180 degrees
```

#### Timing
```python
CAPTURE_PAUSE_DURATION = 0.5      # Seconds to pause after capture
HUD_UPDATE_INTERVAL = 1.0         # Seconds between HUD updates
```

See `settings.py`for the complete list of configurable parameters.

## Development Mode

The project includes a webcam fallback mode for development and testing on non-Raspberry Pi systems.

### Using Webcam Mode

If `picamera2` dependencies are not available, the application automatically falls back to webcam mode:

```bash
# On Windows, macOS, or Linux without picamera2
python main.py
```

**Webcam Mode Features:**
- Uses OpenCV to capture from your default webcam (camera index 0)
- Displays preview in a window with HUD overlay
- Press **SPACE** to capture photos
- Press **Q** to quit
- Web interface works the same as Pi mode
- Photos saved as JPG only (no RAW in webcam mode)

**Controls in Webcam Mode:**
- Physical button: Not available
- Remote shutter: Works via web interface
- Settings: Gain control has limited effect (webcam hardware dependent)

### Installing Development Dependencies

```bash
# Install OpenCV for webcam support
pip install opencv-python
```

This allows you to develop and test the web interface, photo gallery, and application logic without needing Raspberry Pi hardware.

## Troubleshooting

### Camera Not Detected

```bash
# Check if camera is detected
libcamera-hello
```

If the camera is not detected, check your ribbon cable connection and ensure the camera is enabled in `raspi-config`.

### Permission Errors

If you encounter GPIO permission errors, you may need to run with sudo:

```bash
sudo python3 camera.py
```

Or add your user to the `gpio` group:

```bash
sudo usermod -a -G gpio $USER
```

Then log out and back in.

### Preview Not Showing

Ensure you have a display connected via HDMI or DSI. The preview requires a graphical environment.

### Touchscreen Not Working

If touchscreen capture doesn't work:

1. **Check evdev is installed**:
   ```bash
   pip install evdev
   ```

2. **List available input devices**:
   ```bash
   python -c "from evdev import list_devices, InputDevice; [print(f'{d}: {InputDevice(d).name}') for d in list_devices()]"
   ```

3. **Check permissions**: Your user may need to be in the `input` group:
   ```bash
   sudo usermod -a -G input $USER
   ```
   Then log out and back in.

4. **Disable in settings**: Set `TOUCHSCREEN_ENABLED = False` in `settings.py` if you don't have a touchscreen

## API Reference

The Flask web server provides the following REST API endpoints:

### GET /
Returns the main web interface (gallery and settings UI).

### GET /api/photos
Returns a JSON array of photo filenames sorted by date (newest first).

**Response:**
```json
["IMG_20260127_123456.jpg", "IMG_20260127_120000.jpg"]
```

### GET /dcim/<filename>
Serves a photo file from the DCIM directory.

**Example:** `/dcim/IMG_20260127_123456.jpg`

### POST /api/trigger
Triggers the camera shutter to capture a photo.

**Response:**
```json
{"status": "ok", "message": "Shutter requested"}
```

### GET /api/settings
Returns current camera settings.

**Response:**
```json
{
  "gain": 0.0,
  "color_temp": 0
}
```

### POST /api/settings
Updates camera settings. Accepts JSON payload with optional `gain` and `color_temp` fields.

**Request:**
```json
{
  "gain": 2.5,
  "color_temp": 5000
}
```

**Response:**
```json
{
  "status": "ok",
  "gain": 2.5,
  "color_temp": 5000
}
```

**Note:** Set gain or color_temp to 0 for automatic mode.

## File Structure

```
pi-camera/
├── main.py              # Application entry point and thread orchestration
├── digital_camera.py    # Raspberry Pi camera controller (Picamera2)
├── webcam_camera.py     # Webcam fallback implementation (OpenCV)
├── shared_state.py      # Thread-safe state management
├── hud.py               # HUD overlay implementation
├── settings.py          # Configuration settings
├── web/                 # Web interface
│   ├── app.py           # Flask application and API routes
│   ├── static/          # CSS and static assets
│   │   └── styles.css   # Web interface styles
│   └── templates/       # HTML templates
│       └── index.html   # Gallery and settings UI
├── assets/              # Resources (fonts, images)
│   ├── fonts/           # HUD fonts
│   └── hud_grid.png     # Optional HUD background
├── DCIM/                # Photo storage (created automatically)
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## License

This project is open source and available for personal and educational use.

## Acknowledgments

Built using the excellent [picamera2](https://github.com/raspberrypi/picamera2) library from the Raspberry Pi Foundation.
