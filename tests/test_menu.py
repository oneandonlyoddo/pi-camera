"""Touch menu (menu.py), touch mapping (touchscreen.to_screen) and saved settings (CameraState)."""
import json

import pytest

import menu
from settings import CAPTURE_FORMAT_DEFAULT, CAPTURE_FORMATS, CAPTURE_RESOLUTIONS


def centre(rect):
    return (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2


def button_for(state, attr, value):
    return next(rect for rect, _l, _v, _s, action in menu.buttons(state) if action == (attr, value))


def tap(state, attr, value):
    """Tap the visible button whose action is (attr, value)."""
    return menu.handle_tap(state, *centre(button_for(state, attr, value)))


def choose(state, attr, value):
    """Open the menu, the category `attr` and pick `value`, like a user."""
    menu.handle_tap(state, *centre(menu.MENU_BUTTON))
    tap(state, "menu_page", attr)
    tap(state, attr, value)


ATTRS = [attr for _t, attr, _v in menu.categories()]


# --- menu --------------------------------------------------------------------

def test_tap_outside_menu_is_shutter(state):
    assert menu.handle_tap(state, 400, 240) is True
    assert state.menu_open is False


def test_tap_menu_button_opens_category_list(state):
    state.menu_page, state.menu_scroll = "preset", 50  # left over from an earlier visit
    assert menu.handle_tap(state, *centre(menu.MENU_BUTTON)) is False
    assert (state.menu_open, state.menu_page, state.menu_scroll) == (True, "", 0)
    assert menu.title(state) == "SETTINGS"


def test_option_selects_and_returns_to_category_list(state):
    small = CAPTURE_RESOLUTIONS[1]
    choose(state, "capture_resolution", small)
    assert state.capture_resolution == small
    assert (state.menu_open, state.menu_page) == (True, "")
    choose(state, "capture_format", "RAW")
    assert state.capture_format == "RAW"

    tap(state, "menu_open", False)  # DONE
    assert state.menu_open is False


def test_back_returns_without_change(state):
    state.menu_open = True
    tap(state, "menu_page", "capture_format")
    assert menu.title(state) == "FORMAT"
    before = state.snapshot()
    menu.handle_tap(state, *centre(menu.BACK_BUTTON))
    assert (state.menu_page, state.snapshot()) == ("", before)


def test_open_menu_never_fires_shutter(state):
    state.menu_open = True
    assert menu.handle_tap(state, 400, 470) is False  # below the last category row


@pytest.mark.parametrize("page", ["", *ATTRS])
def test_buttons_do_not_overlap_and_fit_the_width(state, page):
    from settings import PREVIEW_WIDTH

    state.menu_open, state.menu_page = True, page
    rects = [rect for rect, *_ in menu.buttons(state)]
    for i, a in enumerate(rects):
        assert 0 <= a[0] < a[2] <= PREVIEW_WIDTH and a[1] >= 0
        for b in rects[i + 1:]:
            assert a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1], (a, b)


def test_defaults_select_one_option_per_page(state):
    expected = {"capture_resolution": CAPTURE_RESOLUTIONS[0], "capture_format": CAPTURE_FORMAT_DEFAULT,
                "preset": "", "colour_temperature": 0, "analogue_gain": 0}
    for attr in ATTRS:
        state.menu_page = attr
        assert [a for _r, _l, _v, sel, a in menu.buttons(state) if sel] == [(attr, expected[attr])]


def test_category_rows_show_current_values(state):
    state.analogue_gain, state.colour_temperature = 3.2, 4200  # web slider values, no menu option
    values = {action[1]: value for _r, _l, value, _s, action in menu.buttons(state)[1:]}
    assert values == {"capture_resolution": "12MP", "capture_format": CAPTURE_FORMAT_DEFAULT, "preset": "NONE",
                      "colour_temperature": "4200K", "analogue_gain": "3.2x"}


def test_gain_steps_select_gain(state):
    choose(state, "analogue_gain", 4.0)
    assert state.analogue_gain == 4.0
    choose(state, "analogue_gain", 0.0)
    assert state.analogue_gain == 0


# --- drag to scroll ----------------------------------------------------------

def long_page(state):
    """Open the WB page (6 options: longer than the screen)."""
    state.menu_open, state.menu_page = True, "colour_temperature"
    assert menu.max_scroll(state) > 0
    return menu.Touch(state)


def test_drag_scrolls_and_does_not_tap(state):
    touch = long_page(state)
    touch.down(400, 400)
    touch.move(400, 300)
    touch.move(400, 200)
    touch.up(400, 200)
    assert state.menu_scroll == min(200, menu.max_scroll(state))
    assert (state.menu_page, state.colour_temperature) == ("colour_temperature", 0)  # nothing chosen


def test_drag_clamps_to_the_list(state):
    touch = long_page(state)
    touch.down(400, 100)
    touch.move(400, 400)  # pull down past the top
    assert state.menu_scroll == 0
    touch.move(400, -2000)
    assert state.menu_scroll == menu.max_scroll(state)


def test_jitter_below_threshold_is_a_tap(state):
    from settings import WB_PRESETS

    touch = long_page(state)
    x, y = centre(button_for(state, "colour_temperature", WB_PRESETS["INDOOR"]))
    assert touch.down(x, y) is False
    touch.move(x + 5, y + menu.DRAG_THRESHOLD - 1)
    touch.up(x + 5, y + menu.DRAG_THRESHOLD - 1)
    assert state.colour_temperature == WB_PRESETS["INDOOR"] and state.menu_page == ""


def test_scrolled_row_is_hit_where_it_is_drawn(state):
    from settings import WB_PRESETS

    long_page(state)
    state.menu_scroll = menu.max_scroll(state)
    tap(state, "colour_temperature", WB_PRESETS["SHADE"])  # the last row, only reachable scrolled
    assert state.colour_temperature == WB_PRESETS["SHADE"]


def test_header_covers_rows_scrolled_beneath_it(state):
    long_page(state)
    state.menu_scroll = menu.ROW_HEIGHT // 2  # first row half under the header
    first = menu.buttons(state)[1]
    assert first[0][1] < menu.LIST_TOP < first[0][3]
    menu.handle_tap(state, menu.DONE_BUTTON[0] - 20, menu.LIST_TOP - 2)  # above the list, on the hidden half
    assert (state.menu_page, state.colour_temperature) == ("colour_temperature", 0)


def test_touch_with_menu_closed_fires_shutter_on_down(state):
    touch = menu.Touch(state)
    assert touch.down(400, 240) is True
    touch.up(400, 240)  # release does nothing more
    assert touch.down(*centre(menu.MENU_BUTTON)) is False and state.menu_open
    touch.up(*centre(menu.MENU_BUTTON))  # the release that opened the menu taps nothing
    assert state.menu_page == ""


def test_resolution_label():
    assert [menu.resolution_label(r) for r in CAPTURE_RESOLUTIONS] == ["12MP", "3MP"]


# --- touch mapping -----------------------------------------------------------

def test_to_screen_scales_and_clamps():
    from touchscreen import to_screen

    rng = (100, 1100)
    assert to_screen(100, 1100, rng, rng, False, False, False) == (0.0, 1.0)
    assert to_screen(600, 350, rng, rng, False, False, False) == (0.5, 0.25)
    assert to_screen(0, 5000, rng, rng, False, False, False) == (0.0, 1.0)


def test_lift_filter_merges_contact_lost_mid_drag():
    """Timings from the log: one drag arrived as downs at .685, .838, .878, .940 s."""
    from touchscreen import LiftFilter

    lift = LiftFilter(0.15)
    out = lift.feed("down", 0.7, 0.71, 0.685)
    out += lift.feed("move", 0.7, 0.65, 0.700)
    out += lift.feed("up", 0.7, 0.60, 0.720)
    out += lift.expire(0.800)  # not due yet
    out += lift.feed("down", 0.7, 0.46, 0.838)
    out += lift.feed("up", 0.7, 0.42, 0.850)
    out += lift.feed("down", 0.7, 0.39, 0.878)
    assert [k for k, *_ in out] == ["down", "move", "move", "move"]  # one touch, never released
    assert lift.timeout(0.9) is None
    out = lift.feed("up", 0.7, 0.33, 0.950)
    assert lift.timeout(1.0) == pytest.approx(0.1)
    assert out == [] and lift.expire(1.050) == [] and lift.expire(1.100) == [("up", 0.7, 0.33)]
    assert lift.timeout(1.2) is None


def test_bounced_drag_through_the_menu_does_not_tap(state):
    """The bug: a gain-page drag broken into short touches chose an option, then opened categories."""
    from touchscreen import LiftFilter

    touch = long_page(state)
    lift = LiftFilter(0.15)
    t, y = 0.0, 400
    events = lift.feed("down", 400, y, t)
    for _ in range(4):  # 4 lost contacts while dragging up
        events += lift.feed("move", 400, y - 10, t + 0.01) + lift.feed("up", 400, y - 10, t + 0.02)
        y, t = y - 40, t + 0.06
        events += lift.feed("down", 400, y, t)
    events += lift.feed("up", 400, y, t + 0.01) + lift.expire(t + 1)
    for kind, x, ey in events:
        getattr(touch, kind)(x, ey)
    assert (state.menu_page, state.colour_temperature) == ("colour_temperature", 0)
    assert state.menu_scroll == menu.max_scroll(state)


def test_to_screen_swap_and_invert():
    from touchscreen import to_screen

    rng = (0, 100)
    assert to_screen(25, 75, rng, rng, True, False, False) == (0.75, 0.25)
    assert to_screen(25, 75, rng, rng, False, True, True) == (0.75, 0.25)


# --- settings persistence + wake ---------------------------------------------

def test_save_load_roundtrip(state, tmp_path):
    from shared_state import CameraState

    path = tmp_path / "s.json"
    state.analogue_gain = 4.0
    state.colour_temperature = 5200
    state.capture_resolution = CAPTURE_RESOLUTIONS[1]
    state.capture_format = "JPG"
    state.save(path)

    loaded = CameraState()
    loaded.load(path)
    assert loaded.snapshot() == state.snapshot()


def test_load_missing_file_keeps_defaults(state, tmp_path):
    before = state.snapshot()
    state.load(tmp_path / "nope.json")
    assert state.snapshot() == before


@pytest.mark.parametrize("content", ["not json", "[1, 2]", ""])
def test_load_corrupt_file_keeps_defaults(state, tmp_path, content):
    path = tmp_path / "s.json"
    path.write_text(content)
    before = state.snapshot()
    state.load(path)
    assert state.snapshot() == before


def test_load_skips_invalid_values(state, tmp_path):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({
        "analogue_gain": 99, "colour_temperature": True,
        "capture_resolution": [640, 480], "capture_format": "TIFF",
    }))
    before = state.snapshot()
    state.load(path)
    assert state.snapshot() == before


def test_every_format_has_capture_streams():
    from digital_camera import CAPTURE_STREAMS

    assert set(CAPTURE_STREAMS) == set(CAPTURE_FORMATS)
    for streams in CAPTURE_STREAMS.values():
        assert streams in (["main"], ["raw"], ["main", "raw"])  # the order tested on the device


@pytest.mark.parametrize("attr, value", [
    ("menu_open", True), ("capture_format", "RAW"), ("analogue_gain", 2.0),
])
def test_setting_change_wakes_loop(state, attr, value):
    import time

    state.wait(0)  # clear
    setattr(state, attr, value)
    t0 = time.monotonic()
    state.wait(2)
    assert time.monotonic() - t0 < 1


def test_wb_option_sets_colour_temperature(state):
    from settings import WB_PRESETS

    choose(state, "colour_temperature", WB_PRESETS["SUNNY"])
    assert state.colour_temperature == WB_PRESETS["SUNNY"]
    state.colour_temperature = 4200  # from the web slider: no WB option selected
    state.menu_page = "colour_temperature"
    assert not any(sel for _r, _l, _v, sel, _a in menu.buttons(state))


@pytest.mark.parametrize("page", ["", *ATTRS])
def test_labels_fit_their_buttons(state, page):
    from PIL import ImageFont

    from settings import HUD_FONT_PATH, HUD_FONT_SIZE

    font = ImageFont.truetype(str(HUD_FONT_PATH), HUD_FONT_SIZE)
    state.menu_open, state.menu_page = True, page
    state.menu_scroll = 10_000  # clamped: also checks the bottom rows
    for rect, label, value, _s, _a in menu.buttons(state):
        assert font.getlength(label) + font.getlength(value) < rect[2] - rect[0] - 48, label
