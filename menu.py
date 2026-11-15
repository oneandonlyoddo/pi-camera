"""Touch menu: layout and tap handling, no camera.

Coordinates are HUD pixels as the user sees the screen (PREVIEW_WIDTH x PREVIEW_HEIGHT,
before the PREVIEW_ROTATE flip). hud.py draws from the same layout, so what you see is what you hit.
"""
import presets
from settings import CAPTURE_FORMATS, CAPTURE_RESOLUTIONS, PREVIEW_HEIGHT, PREVIEW_WIDTH, WB_PRESETS

MENU_BUTTON = (684, 434, 794, 474)  # drawn bottom right, centred in the bottom bar (HUD_BAR_HEIGHT)
MENU_HIT = (620, 380, 800, 480)  # larger than drawn: a finger on a 3.5" resistive screen
PANEL = (0, 0, PREVIEW_WIDTH, PREVIEW_HEIGHT)  # full screen: solid colours, no preview slivers beside the bars
ROW_RESOLUTION_Y = 94  # top of the option buttons; the label sits above
ROW_FORMAT_Y = 196
ROW_PRESET_Y = 298
ROW_WB_Y = 400
ROW_HEIGHT = 64
DONE_BUTTON = (600, 8, 784, 56)  # top right, beside the SETTINGS title; right edge aligned with the option rows


def resolution_label(size):
    """(4056, 3040) -> '12MP'."""
    return f"{round(size[0] * size[1] / 1e6)}MP"


def _row(y, attr, values, labels, current):
    """Equal-width option buttons across the panel: (rect, label, selected, (attr, value))."""
    left, right, gap = PANEL[0] + 16, PANEL[2] - 16, 12
    width = (right - left - gap * (len(values) - 1)) / len(values)
    return [
        ((round(left + i * (width + gap)), y, round(left + i * (width + gap) + width), y + ROW_HEIGHT),
         label, value == current, (attr, value))
        for i, (value, label) in enumerate(zip(values, labels, strict=True))
    ]


def buttons(state):
    """Every menu button, for drawing and hit testing."""
    return (
        _row(ROW_RESOLUTION_Y, "capture_resolution", CAPTURE_RESOLUTIONS,
             [f"{resolution_label(r)} {r[0]}x{r[1]}" for r in CAPTURE_RESOLUTIONS], state.capture_resolution)
        + _row(ROW_FORMAT_Y, "capture_format", CAPTURE_FORMATS, CAPTURE_FORMATS, state.capture_format)
        # shortcut: one row of buttons; past ~4 presets the labels stop fitting, page the row then
        + _row(ROW_PRESET_Y, "preset", ("", *presets.PRESETS), ("NONE", *presets.PRESETS), state.preset)
        # a slider value from the web that is no WB preset selects nothing
        + _row(ROW_WB_Y, "colour_temperature", tuple(WB_PRESETS.values()), tuple(WB_PRESETS), state.colour_temperature)
        + [(DONE_BUTTON, "DONE", True, ("menu_open", False))]
    )


def _inside(rect, x, y):
    return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


def handle_tap(state, x, y):
    """Touch-thread entry: only writes CameraState (R2). Returns True if the tap is a shutter press."""
    if not state.menu_open:
        if _inside(MENU_HIT, x, y):
            state.menu_open = True
            return False
        return True
    for rect, _label, _selected, (attr, value) in buttons(state):
        if _inside(rect, x, y):
            setattr(state, attr, value)
    return False  # taps in the open menu never fire the shutter
