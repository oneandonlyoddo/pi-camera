"""Touch menu (menu.py), touch mapping (touchscreen.to_screen) and saved settings (CameraState)."""
import json

import pytest

import menu
from settings import CAPTURE_FORMAT_DEFAULT, CAPTURE_FORMATS, CAPTURE_RESOLUTIONS


def centre(rect):
    return (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2


def button_for(state, attr, value):
    return next(rect for rect, _l, _s, action in menu.buttons(state) if action == (attr, value))


# --- menu --------------------------------------------------------------------

def test_tap_outside_menu_is_shutter(state):
    assert menu.handle_tap(state, 400, 240) is True
    assert state.menu_open is False


def test_tap_menu_button_opens_menu(state):
    assert menu.handle_tap(state, *centre(menu.MENU_BUTTON)) is False
    assert state.menu_open is True


def test_menu_selects_resolution_and_format_then_closes(state):
    state.menu_open = True
    small = CAPTURE_RESOLUTIONS[1]
    assert menu.handle_tap(state, *centre(button_for(state, "capture_resolution", small))) is False
    assert menu.handle_tap(state, *centre(button_for(state, "capture_format", "RAW"))) is False
    assert (state.capture_resolution, state.capture_format) == (small, "RAW")
    assert state.menu_open is True

    menu.handle_tap(state, *centre(menu.DONE_BUTTON))
    assert state.menu_open is False


def test_open_menu_never_fires_shutter(state):
    state.menu_open = True
    assert menu.handle_tap(state, 400, 470) is False  # empty panel area


def test_buttons_do_not_overlap_and_fit_the_screen(state):
    from settings import PREVIEW_HEIGHT, PREVIEW_WIDTH

    rects = [rect for rect, *_ in menu.buttons(state)]
    for i, a in enumerate(rects):
        assert 0 <= a[0] < a[2] <= PREVIEW_WIDTH and 0 <= a[1] < a[3] <= PREVIEW_HEIGHT
        for b in rects[i + 1:]:
            assert a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1], (a, b)


def test_one_option_selected_per_row(state):
    selected = [action for _r, _l, sel, action in menu.buttons(state) if sel and action[0] != "menu_open"]
    assert selected == [("capture_resolution", CAPTURE_RESOLUTIONS[0]), ("capture_format", CAPTURE_FORMAT_DEFAULT),
                        ("preset", "")]


def test_resolution_label():
    assert [menu.resolution_label(r) for r in CAPTURE_RESOLUTIONS] == ["12MP", "3MP"]


# --- touch mapping -----------------------------------------------------------

def test_to_screen_scales_and_clamps():
    from touchscreen import to_screen

    rng = (100, 1100)
    assert to_screen(100, 1100, rng, rng, False, False, False) == (0.0, 1.0)
    assert to_screen(600, 350, rng, rng, False, False, False) == (0.5, 0.25)
    assert to_screen(0, 5000, rng, rng, False, False, False) == (0.0, 1.0)


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

