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
PREVIEW_WIDTH = 1640
PREVIEW_HEIGHT = 1232

# Capture resolution (for high-res still images)
CAPTURE_WIDTH = 4056
CAPTURE_HEIGHT = 3040

# Fullscreen preview window size
PREVIEW_WINDOW_WIDTH = 1920
PREVIEW_WINDOW_HEIGHT = 1080
PREVIEW_WINDOW_X = 0
PREVIEW_WINDOW_Y = 0

# ============================================================================
# CAMERA TIMING
# ============================================================================
CAPTURE_PAUSE_DURATION = 0.5  # Seconds to pause after capture before returning to preview
HUD_UPDATE_INTERVAL = 1.0  # Seconds between HUD updates

# ============================================================================
# HUD (HEADS-UP DISPLAY) SETTINGS
# ============================================================================
# Font settings
HUD_FONT_PATH_LARGE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
HUD_FONT_PATH_SMALL = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
HUD_FONT_SIZE_LARGE = 32  # Font size for time display
HUD_FONT_SIZE_SMALL = 24  # Font size for date display

# Date/Time format strings
HUD_DATE_FORMAT = "%Y-%m-%d"  # Date format (YYYY-MM-DD)
HUD_TIME_FORMAT = "%H:%M:%S"  # Time format (HH:MM:SS)

# HUD positioning
HUD_PADDING = 20  # Padding from screen edges in pixels
HUD_BACKGROUND_PADDING = 10  # Padding around text background
HUD_TEXT_SPACING = 5  # Spacing between time and date text

# HUD colors (RGBA format: Red, Green, Blue, Alpha)
HUD_COLOR_BACKGROUND = (0, 0, 0, 128)  # Semi-transparent black background
HUD_COLOR_TIME_TEXT = (255, 255, 255, 255)  # White text for time
HUD_COLOR_DATE_TEXT = (200, 200, 200, 255)  # Light gray text for date
HUD_COLOR_SHADOW = (0, 0, 0, 200)  # Black shadow for text
HUD_SHADOW_OFFSET = 2  # Pixel offset for text shadow