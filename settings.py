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
GPIO_DEBOUNCE_TIME = 0.02  # seconds the contact must be stable before a press fires (lgpio); longer drops quick taps
GPIO_CONNECTED = False

# ============================================================================
# TOUCHSCREEN CONFIGURATION
# ============================================================================
TOUCHSCREEN_ENABLED = True  # Enable touchscreen shutter + menu (requires evdev)
# Calibration: map the raw touch axes onto the screen as the user sees it (docs/SPECS.md).
# Every tap is logged with its screen position; tap the corners to check.
TOUCH_SWAP_XY = False
TOUCH_INVERT_X = True
TOUCH_INVERT_Y = True
TOUCH_LIFT_GRACE = 0.15  # s; a lift shorter than this is contact lost mid-drag, not a release (touchscreen.LiftFilter)

# ============================================================================
# FILE PATHS
# ============================================================================
PHOTOS_DIR = PROJECT_ROOT / "DCIM"  # Directory to save captured photos
THUMBNAILS_DIR = PHOTOS_DIR / "thumbs"  # Directory for thumbnail cache
FILENAME_PREFIX = "IMG"  # Prefix for saved image files
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S_%f"  # %f (microseconds): two shots never share a name (R11)
JPG_EXTENSION = ".jpg"  # JPEG file extension
RAW_EXTENSION = ".dng"  # RAW (DNG) file extension
EXIF_ARTIST = ""  # every photo's Artist tag; empty = not written. Visible to anyone you share photos with
EXIF_COPYRIGHT = ""  # e.g. "(c) 2026 Your Name"; empty = not written. ASCII only (others become "?")
SETTINGS_FILE = PROJECT_ROOT / "camera_settings.json"  # gain, WB, resolution, format; restored at startup

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

# Capture resolutions offered in the touch menu; the first is the default.
# Only IMX477 sensor modes with the full field of view, so the DNG matches the JPG.
CAPTURE_RESOLUTIONS = ((4056, 3040), (2028, 1520))
CAPTURE_FORMATS = ("JPG", "RAW", "JPG+RAW")  # RAW = DNG
CAPTURE_FORMAT_DEFAULT = "JPG+RAW"

# Fullscreen preview window size
PREVIEW_WINDOW_X = 0
PREVIEW_WINDOW_Y = 0

PREVIEW_ROTATE = True  # rotate preview + HUD 180° for the upside-down display; never saved photos (docs/SPECS.md)

# ============================================================================
# CAMERA TIMING
# ============================================================================
HUD_UPDATE_INTERVAL = 1.0  # Seconds between HUD updates (a shutter request or setting change wakes the loop early)

# ============================================================================
# RUNTIME SETTINGS (set from the web interface; 0 = auto; saved in SETTINGS_FILE)
# ============================================================================
GAIN_MIN = 1.0  # Analogue gain range of the HQ camera
GAIN_MAX = 16.0
COLOUR_TEMP_MIN = 2000  # Colour temperature range in Kelvin
COLOUR_TEMP_MAX = 8000
# Named WB shortcuts for the colour temperature (touch menu, web, preset "wb"); fixed Kelvin like other cameras.
# Names must fit a menu button, max ~7 characters (tests/test_menu.py checks). 0 = auto.
WB_PRESETS = {"AUTO": 0, "INDOOR": 3000, "FLUOR": 4000, "SUNNY": 5500, "CLOUDY": 6500, "SHADE": 7500}
GAIN_STEPS = (0.0, 1.0, 2.0, 4.0, 8.0, 16.0)  # touch menu + web chips; the web slider sets any value in range

# ============================================================================
# PRESETS (film simulation recipes; chosen in the touch menu, saved in SETTINGS_FILE)
# ============================================================================
PRESETS_FILE = PROJECT_ROOT / "presets.json"  # {name: {color, mono, highlight, shadow, sharpness, wb_red, wb_blue, exposure}}
PRESET_NAME_MAX = 12  # characters; longer names don't fit a menu button
TUNING_FILE = "imx477.json"  # libcamera tuning file the presets modify (HQ camera)
# What one Fuji recipe step does. Guesses to tune by eye against docs/presets/ sample shots.
PRESET_COLOR_STEP = 0.1  # Saturation per "color" step (1.0 = neutral)
PRESET_SHARPNESS_STEP = 0.25  # Sharpness per step (1.0 = neutral)
PRESET_TONE_STEP = 0.02  # max tone curve shift per highlight/shadow step, fraction of full output
PRESET_WB_STEP = 0.05  # red/blue gain factor per WB shift step

# ============================================================================
# HUD (HEADS-UP DISPLAY) SETTINGS
# ============================================================================
# Font settings
HUD_FONT_PATH = PROJECT_ROOT / "assets" / "fonts" / "JetBrainsMono-Medium.ttf"
HUD_FONT_SIZE = 24

# Date/Time format strings
HUD_TIME_FORMAT = "%H:%M - %d/%m/%Y"  # Time format (HH:MM | DD/MM/YYYY)

# HUD positioning
HUD_PADDING_W = 6  # Padding from the left/right screen edges in pixels (text is centred in the bars vertically)

# HUD colours: only the four from docs/design/colour_scheme.jpg, solid (no transparency; docs/design/hud.md)
HUD_COLOR_ACCENT = (0xFF, 0x4D, 0x00)  # FF4D00: MENU button, selected option
HUD_COLOR_DARK = (0x11, 0x11, 0x11)  # 111111: top/bottom bars, menu background, text on accent
HUD_COLOR_LIGHT = (0xF2, 0xF2, 0xF2)  # F2F2F2: data fields, grid, menu text
HUD_COLOR_GREY = (0x8E, 0x8E, 0x8E)  # 8E8E8E: menu labels, unselected outline

# HUD layout
HUD_GRID_WIDTH = 2  # rule-of-thirds lines, px in the 800x480 HUD; the panel shows it at 0.6x
HUD_BAR_HEIGHT = 52  # top and bottom bars behind the data fields; the bottom one holds the MENU button