# Raspberry Pi Zero Digital Camera

A simple digital camera implementation using the Raspberry Pi HQ Camera module. This project turns your Raspberry Pi into a fully functional digital camera with hardware button control, fullscreen preview, and high-quality image capture in both JPG and RAW formats.

## Features

- 📸 **Hardware Shutter Button** - Physical button trigger via GPIO
- 🖥️ **Fullscreen Preview** - Live camera preview on connected display
- 📷 **High-Resolution Capture** - Full 4056x3040 resolution (12.3 MP)
- 🎞️ **Dual Format Saving** - Captures both JPG and RAW (DNG) formats
- ⚡ **Auto-Focus Support** - Continuous autofocus when available
- 🕒 **Timestamped Files** - Automatic filename generation with timestamps
- 📊 **HUD Overlay** - Real-time date and time display on preview

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
cd ~
git clone <repository-url> pi-camera-ai
cd pi-camera-ai
```

Or download the files directly to your Raspberry Pi.

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note:** These dependencies are Raspberry Pi-specific and must be installed on the Pi itself.

### 3. Enable Camera Interface

Ensure the camera interface is enabled on your Raspberry Pi:

```bash
sudo raspi-config
```

Navigate to: **Interface Options** → **Legacy Camera** → **Disable** (use the new camera stack)

Then enable the camera:
**Interface Options** → **Camera** → **Enable**

Reboot your Pi:
```bash
sudo reboot
```

## Usage

### Run the Camera

```bash
python3 camera.py
```

Or make it executable and run directly:

```bash
chmod +x camera.py
./camera.py
```

### Taking Photos

1. The camera will start with a fullscreen preview
2. Press the hardware button to capture a photo
3. Photos are saved to `~/Pictures/pi-camera/` by default
4. Each capture creates two files:
   - `IMG_YYYYMMDD_HHMMSS.jpg` - JPEG image
   - `IMG_YYYYMMDD_HHMMSS.dng` - RAW DNG file

### Exit the Application

Press `Ctrl+C` to safely shut down the camera.

## Configuration

All configurable settings are centralized in [`settings.py`](file:///c:/Users/jonas/Workspace/Personal/pi-camera-ai/settings.py). You can customize the camera behavior by editing this file.

### Key Settings Categories

#### GPIO Configuration
```python
GPIO_BUTTON_PIN = 17              # GPIO pin for shutter button (BCM numbering)
GPIO_DEBOUNCE_TIME = 300          # Button debounce time in milliseconds
```

#### File Paths and Naming
```python
PHOTOS_DIR = Path.home() / "Pictures" / "pi-camera"  # Photo save location
FILENAME_PREFIX = "IMG"           # Prefix for saved image files
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"  # Timestamp format
```

#### Camera Resolution
```python
# Preview resolution (for live view)
PREVIEW_WIDTH = 1640
PREVIEW_HEIGHT = 1232

# Capture resolution (for high-res still images)
CAPTURE_WIDTH = 4056
CAPTURE_HEIGHT = 3040

# Fullscreen preview window size
PREVIEW_WINDOW_WIDTH = 1920
PREVIEW_WINDOW_HEIGHT = 1080
```

#### HUD (Heads-Up Display)
```python
HUD_FONT_SIZE_LARGE = 32          # Font size for time display
HUD_FONT_SIZE_SMALL = 24          # Font size for date display
HUD_PADDING = 20                  # Padding from screen edges
HUD_COLOR_TIME_TEXT = (255, 255, 255, 255)  # White text (RGBA)
HUD_COLOR_DATE_TEXT = (200, 200, 200, 255)  # Light gray text (RGBA)
```

#### Timing
```python
CAPTURE_PAUSE_DURATION = 0.5      # Seconds to pause after capture
HUD_UPDATE_INTERVAL = 1.0         # Seconds between HUD updates
```

See [`settings.py`](file:///c:/Users/jonas/Workspace/Personal/pi-camera-ai/settings.py) for the complete list of configurable parameters.

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

## File Structure

```
pi-camera-ai/
├── camera.py          # Main camera application
├── settings.py        # Configuration settings
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## License

This project is open source and available for personal and educational use.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Acknowledgments

Built using the excellent [picamera2](https://github.com/raspberrypi/picamera2) library from the Raspberry Pi Foundation.
