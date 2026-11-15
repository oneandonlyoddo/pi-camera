"""R4: paths must not depend on the working directory."""
from pathlib import Path

import pytest

from conftest import ROOT


@pytest.mark.parametrize(
    "name, expected",
    [
        ("PHOTOS_DIR", ROOT / "DCIM"),
        ("THUMBNAILS_DIR", ROOT / "DCIM" / "thumbs"),
        ("HUD_FONT_PATH", ROOT / "assets" / "fonts" / "JetBrainsMono-Medium.ttf"),    ],
)
def test_settings_paths_independent_of_cwd(tmp_path, monkeypatch, name, expected):
    import settings

    monkeypatch.chdir(tmp_path)
    assert Path(getattr(settings, name)).resolve() == expected.resolve()
