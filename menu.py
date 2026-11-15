"""Touch menu: layout, tap and drag handling, no camera.

Coordinates are HUD pixels as the user sees the screen (PREVIEW_WIDTH x PREVIEW_HEIGHT,
before the PREVIEW_ROTATE flip). hud.py draws from the same layout, so what you see is what you hit.

Pages: the category list (state.menu_page == "") and one option page per setting
(state.menu_page == the CameraState attribute). Both scroll by dragging (state.menu_scroll).
"""
import presets
from settings import (
    CAPTURE_FORMATS,
    CAPTURE_RESOLUTIONS,
    GAIN_STEPS,
    PREVIEW_HEIGHT,
    PREVIEW_WIDTH,
    WB_PRESETS,
)

MENU_BUTTON = (684, 434, 794, 474)  # drawn bottom right, centred in the bottom bar (HUD_BAR_HEIGHT)
MENU_HIT = (620, 380, 800, 480)  # larger than drawn: a finger on a 3.5" resistive screen
PANEL = (0, 0, PREVIEW_WIDTH, PREVIEW_HEIGHT)  # full screen: solid colours, no preview slivers beside the bars
LIST_TOP = 72  # the header (title, DONE / BACK) sits above; list rows scroll beneath it
ROW_HEIGHT = 64
ROW_GAP = 12
ROW_LEFT, ROW_RIGHT = 16, 784
DONE_BUTTON = (600, 8, 784, 56)  # top right, beside the SETTINGS title; right edge aligned with the rows
BACK_BUTTON = (16, 8, 176, 56)  # top left on an option page
DRAG_THRESHOLD = 16  # px a finger must move before a touch is a drag, not a tap (resistive jitter)


def resolution_label(size):
    """(4056, 3040) -> '12MP'."""
    return f"{round(size[0] * size[1] / 1e6)}MP"


def categories():
    """(title, CameraState attribute, values) per settings category, in menu order."""
    return (
        ("RESOLUTION", "capture_resolution", CAPTURE_RESOLUTIONS),
        ("FORMAT", "capture_format", CAPTURE_FORMATS),
        ("PRESET", "preset", ("", *presets.PRESETS)),
        ("WHITE BALANCE", "colour_temperature", tuple(WB_PRESETS.values())),
        ("GAIN", "analogue_gain", GAIN_STEPS),
    )


def value_label(attr, value):
    """Short text for a setting's value; also covers web slider values that are no menu option."""
    if attr == "capture_resolution":
        return resolution_label(value)
    if attr == "preset":
        return value or "NONE"
    if attr == "colour_temperature":
        return next((name for name, k in WB_PRESETS.items() if k == value), f"{value}K")
    if attr == "analogue_gain":
        return "AUTO" if value == 0 else f"{value:g}x"
    return value


def option_label(attr, value):
    """Text for one option on an option page (and a web chip): the resolution also shows its size."""
    return f"{resolution_label(value)} {value[0]}x{value[1]}" if attr == "capture_resolution" else value_label(attr, value)


def title(state):
    page = state.menu_page
    return next((t for t, attr, _v in categories() if attr == page), "SETTINGS")


def _items(state):
    """The list rows of the current page: (label, value text, selected, (attr, value) to set)."""
    page = state.menu_page
    for _t, attr, values in categories():
        if attr == page:
            current = getattr(state, attr)
            return [(option_label(attr, v), "", v == current, (attr, v)) for v in values]
    return [(t, value_label(attr, getattr(state, attr)), False, ("menu_page", attr)) for t, attr, _v in categories()]


def max_scroll(state):
    content = len(_items(state)) * (ROW_HEIGHT + ROW_GAP) - ROW_GAP + 16  # 16 px below the last row
    return max(0, LIST_TOP + content - PREVIEW_HEIGHT)


def buttons(state):
    """Every visible menu button: (rect, label, value text, selected, (attr, value)).

    The first is the one header button (DONE or BACK), the rest are the visible list rows.
    """
    header = [(DONE_BUTTON, "DONE", "", True, ("menu_open", False))] if state.menu_page == "" else \
        [(BACK_BUTTON, "< BACK", "", False, ("menu_page", ""))]
    top = LIST_TOP - min(state.menu_scroll, max_scroll(state))
    rows = []
    for i, (label, value, selected, action) in enumerate(_items(state)):
        y = top + i * (ROW_HEIGHT + ROW_GAP)
        if y + ROW_HEIGHT > LIST_TOP and y < PREVIEW_HEIGHT:  # at least partly in the list area
            rows.append(((ROW_LEFT, y, ROW_RIGHT, y + ROW_HEIGHT), label, value, selected, action))
    return header + rows


def _inside(rect, x, y):
    return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


def _open(state):
    state.menu_page = ""
    state.menu_scroll = 0
    state.menu_open = True


def handle_tap(state, x, y):
    """A tap (touch thread): only writes CameraState (R2). Returns True if the tap is a shutter press."""
    if not state.menu_open:
        if _inside(MENU_HIT, x, y):
            _open(state)
            return False
        return True
    for i, (rect, _label, _value, _selected, (attr, value)) in enumerate(buttons(state)):
        # a row scrolled partly under the header is hit only below it (i == 0 is the header)
        if _inside(rect, x, y) and (i == 0 or y >= LIST_TOP):
            if attr == "menu_open":
                state.menu_open = False
            elif attr == "menu_page":
                state.menu_scroll = 0
                state.menu_page = value
            else:  # an option: set it and go back to the category list
                setattr(state, attr, value)
                state.menu_scroll = 0
                state.menu_page = ""
            break
    return False  # taps in the open menu never fire the shutter


class Touch:
    """Tap vs. drag for one finger, fed down/move/up by the touch thread; only writes CameraState (R2).

    Menu closed: touch-down acts at once (shutter or MENU), as before. Menu open: a touch that moves
    less than DRAG_THRESHOLD is a tap at its down position on release; otherwise it scrolls the list.
    """

    def __init__(self, state):
        self.state = state
        self.start = None  # (x, y, menu_scroll) at touch-down while the menu is open
        self.dragging = False

    def down(self, x, y):
        """Returns True if the touch is a shutter press."""
        if not self.state.menu_open:
            return handle_tap(self.state, x, y)
        self.start = (x, y, self.state.menu_scroll)
        self.dragging = False
        return False

    def move(self, _x, y):
        if self.start is None:
            return
        dy = y - self.start[1]
        self.dragging = self.dragging or abs(dy) > DRAG_THRESHOLD
        if self.dragging:
            scroll = round(min(max(self.start[2] - dy, 0), max_scroll(self.state)))
            if scroll != self.state.menu_scroll:  # every write wakes the loop for a redraw
                self.state.menu_scroll = scroll

    def up(self, _x, _y):
        if self.start is not None and not self.dragging:
            handle_tap(self.state, *self.start[:2])
        self.start = None
