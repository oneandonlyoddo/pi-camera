"""Presets: presets.json validation, controls and tuning edits, menu row, HUD name, persistence."""
import json

import numpy as np
import pytest

import menu
import presets
from settings import HUD_BAR_HEIGHT, HUD_COLOR_LIGHT, PREVIEW_WIDTH

BASE = {"version": 2.0, "algorithms": [
    {"rpi.awb": {"sensitivity_r": 1.0, "sensitivity_b": 1.0}},
    {"rpi.contrast": {"gamma_curve": [x for i in range(17) for x in (i * 4096 - (i == 16), i * 4096 - (i == 16))]}},
]}


@pytest.fixture
def two_presets(monkeypatch):
    monkeypatch.setattr(presets, "PRESETS", {"Acros": {"mono": True}, "Portra": {"wb_red": 2}})


def test_shipped_presets_file_is_valid():
    raw = json.loads(presets.PRESETS_FILE.read_text(encoding="utf-8"))
    assert presets.load(presets.PRESETS_FILE) == raw and raw


def test_load_skips_invalid(tmp_path):
    path = tmp_path / "p.json"
    path.write_text(json.dumps({
        "Ok": {"color": 2, "mono": False, "wb": 5500},
        "BadKey": {"grain": 1}, "OutOfRange": {"highlight": 5}, "Bool": {"color": True},
        "NotMono": {"mono": 1}, "WbLow": {"wb": 1000}, "WbZero": {"wb": 0}, "WbName": {"wb": "sunset"}, "A very long preset name": {}, "NaN": {"shadow": float("nan")},
    }))
    assert presets.load(path) == {"Ok": {"color": 2, "mono": False, "wb": 5500}}


@pytest.mark.parametrize("content", ["not json", "[1]"])
def test_load_broken_file_gives_none(tmp_path, content):
    path = tmp_path / "p.json"
    path.write_text(content)
    assert presets.load(path) == {}
    assert presets.load(tmp_path / "missing.json") == {}


def test_controls():
    assert presets.controls({}) == {"Saturation": 1.0, "Sharpness": 1.0, "ExposureValue": 0.0}
    assert presets.controls({"mono": True, "color": 4})["Saturation"] == 0.0
    c = presets.controls({"color": 2, "sharpness": -4, "exposure": 0.7})
    assert c == pytest.approx({"Saturation": 1.2, "Sharpness": 0.0, "ExposureValue": 0.7})


def test_tuning_wb_shift_and_base_untouched():
    tuned = presets.tuning(BASE, {"wb_red": 2, "wb_blue": -4})
    awb = tuned["algorithms"][0]["rpi.awb"]
    assert awb["sensitivity_r"] > 1.0 > awb["sensitivity_b"]
    assert BASE["algorithms"][0]["rpi.awb"]["sensitivity_r"] == 1.0
    assert presets.tuning(BASE, {}) == BASE


@pytest.mark.parametrize("highlight, shadow", [(4, 4), (-4, -4), (4, -4), (-4, 4)])
def test_tone_curve_stays_monotonic_with_fixed_ends(highlight, shadow):
    ys = presets.tuning(BASE, {"highlight": highlight, "shadow": shadow})["algorithms"][1]["rpi.contrast"]["gamma_curve"][1::2]
    base = BASE["algorithms"][1]["rpi.contrast"]["gamma_curve"][1::2]
    assert all(a < b for a, b in zip(ys, ys[1:], strict=False))
    assert (ys[0], ys[-1]) == (base[0], base[-1])
    quarter, three_quarter = 4, 12  # y = 0.25 and 0.75 in BASE
    assert np.sign(base[quarter] - ys[quarter]) == np.sign(shadow)  # shadow + darkens
    assert np.sign(ys[three_quarter] - base[three_quarter]) == np.sign(highlight)  # highlight + brightens


def test_menu_row_selects_preset(state, two_presets):
    state.menu_open, state.menu_page = True, "preset"
    labels = [label for _r, label, _v, _s, (attr, _x) in menu.buttons(state) if attr == "preset"]
    assert labels == ["NONE", "Acros", "Portra"]
    rect = next(r for r, _l, _v, _s, action in menu.buttons(state) if action == ("preset", "Portra"))
    menu.handle_tap(state, (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)
    assert state.preset == "Portra" and state.menu_open is True


def test_preset_persists_and_unknown_is_skipped(state, tmp_path, two_presets):
    from shared_state import CameraState

    path = tmp_path / "s.json"
    state.preset = "Acros"
    state.save(path)
    loaded = CameraState()
    loaded.load(path)
    assert loaded.preset == "Acros"

    path.write_text(json.dumps({"preset": "Deleted"}))
    loaded = CameraState()
    loaded.load(path)
    assert loaded.preset == ""


def _top_centre_has_text(state, monkeypatch):
    import hud

    class FakeCamera:
        def capture_metadata(self):
            return {}

        def set_overlay(self, overlay):
            self.overlay = overlay

    monkeypatch.setattr(hud, "PREVIEW_ROTATE", False)
    cam = FakeCamera()
    hud.HUD().update(cam, state)
    strip = cam.overlay[:HUD_BAR_HEIGHT, PREVIEW_WIDTH // 2 - 40:PREVIEW_WIDTH // 2 + 40, :3].reshape(-1, 3)
    return any(tuple(c) == HUD_COLOR_LIGHT for c in strip)


def test_hud_shows_preset_name_top_centre(state, monkeypatch, two_presets):
    assert not _top_centre_has_text(state, monkeypatch)  # none: empty
    state.preset = "Portra"
    assert _top_centre_has_text(state, monkeypatch)


def test_colour_gains_interpolate_clamp_and_shift():
    tuning = {"algorithms": [{"rpi.awb": {"ct_curve": [3000, 0.5, 0.5, 6000, 0.25, 1.0]}}]}
    assert presets.colour_gains(tuning, {"wb": 2000}) == pytest.approx((2.0, 2.0))  # clamped below
    assert presets.colour_gains(tuning, {"wb": 8000}) == pytest.approx((4.0, 1.0))  # clamped above
    plain = presets.colour_gains(tuning, {"wb": 4500})
    shifted = presets.colour_gains(tuning, {"wb": 4500, "wb_red": 2, "wb_blue": -4})
    assert shifted[0] > plain[0] and shifted[1] < plain[1]


def test_wb_by_name(tmp_path):
    path = tmp_path / "p.json"
    path.write_text(json.dumps({"Day": {"wb": "sunny"}, "Auto": {"wb": "Auto", "color": 1}}))
    assert presets.load(path) == {"Day": {"wb": 5500}, "Auto": {"color": 1}}
