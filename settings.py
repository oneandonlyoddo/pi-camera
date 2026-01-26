"""
Camera Settings Configuration
All configurable parameters for the Raspberry Pi Digital Camera.
"""

from pathlib import Path

# ============================================================================
# GPIO CONFIGURATION
# ============================================================================
GPIO_BUTTON_PIN = 26  # GPIO pin for shutter button (BCM numbering)
GPIO_DEBOUNCE_TIME = 0.3  # Button debounce time in seconds
GPIO_CONNECTED = False

# ============================================================================
# FILE PATHS
# ============================================================================
PHOTOS_DIR = Path.home() / "Pictures" / "pi-camera"  # Directory to save captured photos
FILENAME_PREFIX = "IMG"  # Prefix for saved image files
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"  # Timestamp format for filenames
JPG_EXTENSION = ".jpg"  # JPEG file extension
RAW_EXTENSION = ".dng"  # RAW (DNG) file extension

# ============================================================================
# CAMERA RESOLUTION SETTINGS
# ============================================================================
# Preview resolution (for live view)
PREVIEW_WIDTH = 800
PREVIEW_HEIGHT = 480

# Capture resolution (for high-res still images)
CAPTURE_WIDTH = 4056
CAPTURE_HEIGHT = 3040

# Fullscreen preview window size
PREVIEW_WINDOW_X = 0
PREVIEW_WINDOW_Y = 0

PREVIEW_ROTATE = True

# ============================================================================
# CAMERA TIMING
# ============================================================================
CAPTURE_PAUSE_DURATION = 0.5  # Seconds to pause after capture before returning to preview
HUD_UPDATE_INTERVAL = 1.0  # Seconds between HUD updates

# ============================================================================
# HUD (HEADS-UP DISPLAY) SETTINGS
# ============================================================================
# Font settings
HUD_FONT_PATH = "./assets/fonts/JetBrainsMono-Medium.ttf"

# Date/Time format strings
HUD_TIME_FORMAT = "%H:%M | %d/%m/%Y"  # Time format (HH:MM | DD/MM/YYYY)

# HUD positioning
HUD_PADDING = 20  # Padding from screen edges in pixels
HUD_BACKGROUND_PADDING = 10  # Padding around text background

# HUD colors (RGBA format: Red, Green, Blue, Alpha
HUD_COLOR_TEXT = (255, 255, 255, 255)  # White text for time


# HUD Background Image
# Path to a transparent PNG to use as the HUD background (optional)
# Set to None to use the default generated background
HUD_BACKGROUND_IMAGE_PATH = "./assets/hud_grid.png"