"""
Camera Settings Configuration
All configurable parameters for the Raspberry Pi Digital Camera.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent  # all paths below are absolute (R4)

# ============================================================================
# GPIO CONFIGURATION
# ============================================================================
GPIO_BUTTON_PIN = 17  # GPIO pin for shutter button (BCM numbering)
GPIO_DEBOUNCE_TIME = 0.3  # Button debounce time in seconds
GPIO_CONNECTED = False

# ============================================================================
# TOUCHSCREEN CONFIGURATION
# ============================================================================
TOUCHSCREEN_ENABLED = True  # Enable touchscreen shutter trigger (requires evdev)

# ============================================================================
# FILE PATHS
# ============================================================================
PHOTOS_DIR = PROJECT_ROOT / "DCIM"  # Directory to save captured photos
THUMBNAILS_DIR = PHOTOS_DIR / "thumbs"  # Directory for thumbnail cache
FILENAME_PREFIX = "IMG"  # Prefix for saved image files
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S_%f"  # %f (microseconds): two shots never share a name (R11)
JPG_EXTENSION = ".jpg"  # JPEG file extension
RAW_EXTENSION = ".dng"  # RAW (DNG) file extension

# ============================================================================
# THUMBNAIL SETTINGS
# ============================================================================
THUMBNAIL_WIDTH = 300  # Thumbnail width in pixels
THUMBNAIL_HEIGHT = 225  # Thumbnail height in pixels (maintains 4:3 aspect ratio)
THUMBNAIL_QUALITY = 85  # JPEG quality for thumbnails (1-100)

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

PREVIEW_ROTATE = True  # rotate preview + HUD 180° for the upside-down display; never saved photos (docs/SPECS.md)

# ============================================================================
# CAMERA TIMING
# ============================================================================
HUD_UPDATE_INTERVAL = 1.0  # Seconds between HUD updates (a shutter request wakes the loop early)

# ============================================================================
# RUNTIME SETTINGS (set from the web interface; 0 = auto)
# ============================================================================
GAIN_MIN = 1.0  # Analogue gain range of the HQ camera
GAIN_MAX = 16.0
COLOUR_TEMP_MIN = 2000  # Colour temperature range in Kelvin
COLOUR_TEMP_MAX = 8000

# ============================================================================
# HUD (HEADS-UP DISPLAY) SETTINGS
# ============================================================================
# Font settings
HUD_FONT_PATH = PROJECT_ROOT / "assets" / "fonts" / "JetBrainsMono-Medium.ttf"
HUD_FONT_SIZE = 24

# Date/Time format strings
HUD_TIME_FORMAT = "%H:%M - %d/%m/%Y"  # Time format (HH:MM | DD/MM/YYYY)

# HUD positioning
HUD_PADDING_W = 6  # Padding from screen edges in pixels
HUD_PADDING_H = 6

# HUD colors (RGBA format: Red, Green, Blue, Alpha
HUD_COLOR_WHITE = (255, 255, 255, 255)  # White text for time
HUD_COLOR_BLACK = (0, 0, 0, 255)  # Black text for settings

# HUD Background Image
# Path to a transparent PNG to use as the HUD background (optional)
# Set to None to use the default generated background
HUD_BACKGROUND_IMAGE_PATH = PROJECT_ROOT / "assets" / "hud_grid.png"