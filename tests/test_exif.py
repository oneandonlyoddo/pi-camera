"""EXIF tags (exif.py): JPEG via piexif, DNG via pidng, without the camera."""
import datetime
import io

import numpy as np
import piexif
import pytest

import exif

SHOT = datetime.datetime(2026, 11, 15, 14, 3, 7, 123456, tzinfo=datetime.timezone(datetime.timedelta(hours=1)))
METADATA = {
    "ExposureTime": 66661, "AnalogueGain": 4.0, "DigitalGain": 1.25,
    "SensorBlackLevels": (4096, 4096, 4096, 4096), "ColourGains": (2.0, 1.5),
    "ColourCorrectionMatrix": (1, 0, 0, 0, 1, 0, 0, 0, 1), "SensorTimestamp": 123456789,
}


@pytest.fixture
def no_author(monkeypatch):
    monkeypatch.setattr(exif, "EXIF_ARTIST", "")
    monkeypatch.setattr(exif, "EXIF_COPYRIGHT", "")


def jpeg_tags(**kw):
    args = dict(metadata=METADATA, shot_time=SHOT, model="imx477", size=(4056, 3040),
                manual_gain=False, manual_wb=False) | kw
    return piexif.load(piexif.dump(exif.jpeg_exif(**args)))  # roundtrip: piexif accepts every value


def test_jpeg_capture_values(no_author):
    d = jpeg_tags()
    zeroth, ex = d["0th"], d["Exif"]
    assert zeroth[piexif.ImageIFD.Make] == b"Raspberry Pi"
    assert zeroth[piexif.ImageIFD.Model] == b"imx477"
    assert ex[piexif.ExifIFD.DateTimeOriginal] == b"2026:11:15 14:03:07"
    assert ex[piexif.ExifIFD.SubSecTimeOriginal] == b"123456"
    assert ex[piexif.ExifIFD.OffsetTimeOriginal] == b"+01:00"
    assert ex[piexif.ExifIFD.ExposureTime] == (66661, 1_000_000)
    assert ex[piexif.ExifIFD.ISOSpeedRatings] == 500  # 4.0 x 1.25 x 100
    assert ex[piexif.ExifIFD.PixelXDimension] == 4056 and ex[piexif.ExifIFD.PixelYDimension] == 3040
    assert (ex[piexif.ExifIFD.ExposureProgram], ex[piexif.ExifIFD.ExposureMode], ex[piexif.ExifIFD.WhiteBalance]) == (2, 0, 0)


def test_jpeg_manual_modes(no_author):
    ex = jpeg_tags(manual_gain=True, manual_wb=True)["Exif"]
    assert (ex[piexif.ExifIFD.ExposureProgram], ex[piexif.ExifIFD.ExposureMode], ex[piexif.ExifIFD.WhiteBalance]) == (1, 1, 1)


def test_no_aperture_or_lens_tags(no_author):
    """The manual lens can't report them, so nothing is guessed (docs/FEATURES.md)."""
    ex = jpeg_tags()["Exif"]
    for tag in ("FNumber", "ApertureValue", "MaxApertureValue", "FocalLength", "LensModel", "LensMake"):
        assert getattr(piexif.ExifIFD, tag) not in ex
    from pidng.dng import Tag

    dng = [tag for tag, _ in exif.dng_tags(METADATA, SHOT, False)]
    for tag in (Tag.FNumber, Tag.ApertureValue, Tag.MaxApertureValue, Tag.FocalLength, Tag.EXIFPhotoLensModel):
        assert tag not in dng


def test_author_omitted_when_empty(no_author):
    assert piexif.ImageIFD.Artist not in jpeg_tags()["0th"]
    assert piexif.ImageIFD.Copyright not in jpeg_tags()["0th"]


def test_author_written_and_ascii_only(monkeypatch):
    monkeypatch.setattr(exif, "EXIF_ARTIST", "Jörg")
    monkeypatch.setattr(exif, "EXIF_COPYRIGHT", "(c) 2026 Jörg")
    zeroth = jpeg_tags()["0th"]
    assert zeroth[piexif.ImageIFD.Artist] == b"J?rg"
    assert zeroth[piexif.ImageIFD.Copyright] == b"(c) 2026 J?rg"


def encode_dng(tags):
    """A tiny 12-bit packed raw frame through pidng, like DigitalCamera._save_dng."""
    from pidng.camdefs import Picamera2Camera
    from pidng.core import PICAM2DNG

    config = {"size": (16, 8), "format": "SBGGR12_CSI2P", "stride": 24}
    camera = Picamera2Camera(config, METADATA, "imx477")
    for tag, value in tags:
        camera.tags.set(tag, value)
    dng = PICAM2DNG(camera)
    dng.options(compress=0)
    out = io.BytesIO()
    dng.convert(np.zeros((8, 24), dtype=np.uint8), file=out)
    return piexif.load(out.getvalue())["0th"]


def test_dng_tags_written(monkeypatch):
    monkeypatch.setattr(exif, "EXIF_ARTIST", "Jörg")
    monkeypatch.setattr(exif, "EXIF_COPYRIGHT", "")
    zeroth = encode_dng(exif.dng_tags(METADATA, SHOT, manual_gain=True))
    assert zeroth[piexif.ImageIFD.Make] == b"Raspberry Pi"
    assert zeroth[piexif.ImageIFD.DateTime] == b"2026:11:15 14:03:07"
    assert zeroth[piexif.ImageIFD.ExposureTime] == (66661, 1_000_000)
    assert zeroth[piexif.ImageIFD.Artist] == b"J?rg"
    assert piexif.ImageIFD.Copyright not in zeroth


def test_dng_tags_unique():
    tags = [t for t, _ in exif.dng_tags(METADATA, SHOT, False)]
    assert len(tags) == len(set(tags))
    from pidng.dng import Tag

    assert Tag.Software not in tags  # pidng writes its own; a second would duplicate it
