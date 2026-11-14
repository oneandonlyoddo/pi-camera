"""Shared fixtures. Tests run on the Pi via `scripts/dev.sh --test`.

Tests never touch the real DCIM/ (R11): the `dcim` fixture points the
Flask app at a temporary directory.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def dcim(tmp_path, monkeypatch):
    """Temporary DCIM/ and DCIM/thumbs/, wired into web.app."""
    import web.app as webapp

    photos = tmp_path / "DCIM"
    thumbs = photos / "thumbs"
    thumbs.mkdir(parents=True)
    monkeypatch.setattr(webapp, "photos_path", photos)
    monkeypatch.setattr(webapp, "thumbnails_path", thumbs)
    return photos


@pytest.fixture
def state():
    from shared_state import CameraState

    return CameraState()


@pytest.fixture
def client(dcim, state, monkeypatch):
    """Flask test client with a fresh CameraState and a temporary DCIM/."""
    import web.app as webapp

    monkeypatch.setattr(webapp, "camera_state", state)
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


@pytest.fixture
def make_jpg():
    """Write a small solid-colour JPEG to `path`."""
    from PIL import Image

    def _make(path, size=(640, 480)):
        Image.new("RGB", size, (200, 100, 50)).save(path, "JPEG")
        return path

    return _make
