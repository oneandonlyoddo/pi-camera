"""Web API contract (README "API Reference") and R7."""
import os

import pytest


# --- /api/photos -------------------------------------------------------------

def test_photos_empty(client):
    assert client.get("/api/photos").get_json() == []


def test_photos_lists_jpgs_newest_first(client, dcim, make_jpg):
    old = make_jpg(dcim / "IMG_old.jpg")
    new = make_jpg(dcim / "IMG_new.jpg")
    (dcim / "IMG_new.dng").write_bytes(b"raw")
    os.utime(old, (1_000_000, 1_000_000))
    os.utime(new, (2_000_000, 2_000_000))

    assert client.get("/api/photos").get_json() == ["IMG_new.jpg", "IMG_old.jpg"]


# --- /dcim/<filename> --------------------------------------------------------

def test_serve_photo_with_cache_header(client, dcim, make_jpg):
    make_jpg(dcim / "IMG_a.jpg")
    res = client.get("/dcim/IMG_a.jpg")
    assert res.status_code == 200
    assert res.cache_control.max_age == 31536000


def test_serve_missing_photo_404(client):
    assert client.get("/dcim/nope.jpg").status_code == 404


# --- /dcim/thumbs/<filename> -------------------------------------------------

def test_thumbnail_generated_on_demand(client, dcim, make_jpg):
    from PIL import Image

    make_jpg(dcim / "IMG_a.jpg", size=(4056, 3040))
    res = client.get("/dcim/thumbs/IMG_a.jpg")

    assert res.status_code == 200
    thumb = dcim / "thumbs" / "IMG_a.jpg"
    assert thumb.exists()
    with Image.open(thumb) as img:
        assert img.width <= 300 and img.height <= 225


def test_thumbnail_for_missing_original_404(client):
    assert client.get("/dcim/thumbs/nope.jpg").status_code == 404


def test_thumbnail_rejects_path_outside_dcim(client, dcim, make_jpg, tmp_path):
    import web.app as webapp

    make_jpg(tmp_path / "outside.jpg")
    with pytest.raises(FileNotFoundError):
        webapp.generate_thumbnail_if_missing("../outside.jpg")
    assert not (dcim / "outside.jpg").exists()


# --- /api/trigger ------------------------------------------------------------

def test_trigger_requests_shutter(client, state):
    res = client.post("/api/trigger")
    assert res.get_json()["status"] == "ok"
    assert state.consume_shutter_request() is True


# --- /api/settings -----------------------------------------------------------

def test_settings_roundtrip(client):
    from settings import CAPTURE_FORMAT_DEFAULT, CAPTURE_RESOLUTIONS

    expected = {"gain": 2.5, "color_temp": 5000, "resolution": list(CAPTURE_RESOLUTIONS[0]),
                "format": CAPTURE_FORMAT_DEFAULT, "preset": ""}
    res = client.post("/api/settings", json={"gain": 2.5, "color_temp": 5000})
    assert res.get_json() == {"status": "ok", **expected}
    assert client.get("/api/settings").get_json() == expected


def test_settings_sets_resolution_format_preset(client, state):
    import presets
    from settings import CAPTURE_RESOLUTIONS

    small = CAPTURE_RESOLUTIONS[1]
    name = next(iter(presets.PRESETS))
    res = client.post("/api/settings", json={"resolution": list(small), "format": "RAW", "preset": name})
    assert res.status_code == 200
    assert (state.capture_resolution, state.capture_format, state.preset) == (small, "RAW", name)
    client.post("/api/settings", json={"preset": ""})
    assert state.preset == ""


def test_settings_zero_means_auto(client, state):
    client.post("/api/settings", json={"gain": 3.0, "color_temp": 4000})
    client.post("/api/settings", json={"gain": 0, "color_temp": 0})
    assert state.analogue_gain == 0.0
    assert state.colour_temperature == 0


def test_settings_empty_body_400(client):
    assert client.post("/api/settings", json={}).status_code == 400


@pytest.mark.parametrize(
    "payload",
    [
        {"gain": -5},
        {"gain": 100},
        {"gain": "nan"},
        {"gain": "inf"},
        {"gain": 0.5},
        {"gain": True},
        {"gain": "abc"},
        {"gain": None},
        {"color_temp": -1},
        {"color_temp": 500},
        {"color_temp": 50000},
        {"color_temp": True},
        {"gain": 2.0, "color_temp": 50000},  # one bad value rejects the whole request
        {"resolution": [640, 480]},
        {"resolution": "4056x3040"},
        {"resolution": 12},
        {"resolution": [[4056], [3040]]},
        {"format": "TIFF"},
        {"format": ["RAW"]},
        {"preset": "Deleted"},
        {"preset": {"a": 1}},
        {"preset": None},
        {"gain": 2.0, "format": "TIFF"},
    ],
)
def test_settings_rejects_out_of_range(client, state, payload):
    before = state.snapshot()
    res = client.post("/api/settings", json=payload)
    assert res.status_code == 400
    assert state.snapshot() == before


def test_settings_rejects_non_object_body(client):
    assert client.post("/api/settings", json=[1, 2]).status_code == 400


def test_settings_page_renders_every_menu_option(client):
    """Each touch-menu option is a chip on the web page, and its value passes the API."""
    import html as html_lib
    import json
    import re

    import menu

    page = client.get("/").get_data(as_text=True)
    chips = {(key, json.dumps(json.loads(html_lib.unescape(value))))  # normalised JSON: lists don't hash
             for key, value in re.findall(r'data-key="(\w+)" data-value="([^"]*)"', page)}
    api_key = {"capture_resolution": "resolution", "capture_format": "format", "preset": "preset",
               "colour_temperature": "color_temp", "analogue_gain": "gain"}
    for _t, attr, values in menu.categories():
        for v in values:
            key, value = api_key[attr], list(v) if isinstance(v, tuple) else v
            assert (key, json.dumps(value)) in chips, (key, value)
            assert client.post("/api/settings", json={key: value}).status_code == 200, (key, value)
