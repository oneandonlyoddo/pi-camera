"""HUD rendering without a camera: layout and colours (docs/design/hud.md)."""
import numpy as np
import pytest

import menu
from settings import (
    HUD_BAR_HEIGHT,
    HUD_COLOR_ACCENT,
    HUD_COLOR_DARK,
    HUD_COLOR_LIGHT,
    PREVIEW_HEIGHT,
    PREVIEW_WIDTH,
)


class FakeCamera:
    def capture_metadata(self):
        return {"ExposureTime": 12345, "AnalogueGain": 1.5, "ColourTemperature": 5200}

    def set_overlay(self, overlay):
        self.overlay = overlay


@pytest.fixture
def render(state, monkeypatch):
    """Render the HUD unrotated (as the user sees it) and return the RGBA array."""
    import hud

    monkeypatch.setattr(hud, "PREVIEW_ROTATE", False)

    def _render():
        cam = FakeCamera()
        hud.HUD().update(cam, state)
        assert cam.overlay.shape == (PREVIEW_HEIGHT, PREVIEW_WIDTH, 4)
        return cam.overlay

    return _render


def test_grid_lines_at_thirds(render):
    img = render()
    x, y = PREVIEW_WIDTH // 3, PREVIEW_HEIGHT // 2
    assert tuple(img[y, x]) == (*HUD_COLOR_LIGHT, 255)
    assert img[y, x + 20, 3] == 0  # the preview shows between lines


@pytest.mark.parametrize("menu_open", [False, True])
def test_no_transparency(render, state, menu_open):
    """docs/design/hud.md: solid colours only. Every pixel is fully transparent or fully opaque."""
    state.menu_open = menu_open
    alpha = render()[..., 3]
    assert set(np.unique(alpha)) <= {0, 255}


def test_bars_cover_the_grid(render):
    img = render()
    x = PREVIEW_WIDTH // 3  # a grid column
    for y in (2, HUD_BAR_HEIGHT - 2, PREVIEW_HEIGHT - HUD_BAR_HEIGHT + 2, PREVIEW_HEIGHT - 2):
        assert tuple(img[y, x]) == (*HUD_COLOR_DARK, 255), y


def test_menu_button_bottom_right_in_accent(render):
    img = render()
    cx = menu.MENU_BUTTON[0] + 4  # left edge inside the button, away from the label
    cy = (menu.MENU_BUTTON[1] + menu.MENU_BUTTON[3]) // 2
    assert tuple(img[cy, cx, :3]) == HUD_COLOR_ACCENT
    assert cx > PREVIEW_WIDTH / 2 and cy > PREVIEW_HEIGHT / 2


def test_bottom_data_fields_light_on_dark_bar(render):
    img = render()
    strip = img[PREVIEW_HEIGHT - HUD_BAR_HEIGHT:, :menu.MENU_BUTTON[0] - 10, :3].reshape(-1, 3)
    colours = {tuple(c) for c in np.unique(strip, axis=0)}
    assert HUD_COLOR_DARK in colours and HUD_COLOR_LIGHT in colours  # bar + text


def test_menu_open_renders(render, state):
    state.menu_open = True
    img = render()
    rect = next(r for r, _l, sel, _a in menu.buttons(state) if sel)
    assert tuple(img[rect[1] + 20, rect[0] + 4, :3]) == HUD_COLOR_ACCENT
    # MENU button (partly outside the panel) is hidden while the menu is open
    assert tuple(img[menu.MENU_BUTTON[3] - 2, menu.MENU_BUTTON[2] - 12, :3]) != HUD_COLOR_ACCENT
    assert np.any(img[..., 3] > 0)
