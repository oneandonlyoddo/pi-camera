"""EXIF tags for saved photos, without the camera.

Only values measured at capture or reported by the sensor (docs/FEATURES.md): no aperture
or lens tags, because the manual lens can't report them. Artist/Copyright come from settings.py.
"""
import piexif
from pidng.dng import Tag
from settings import EXIF_ARTIST, EXIF_COPYRIGHT

MAKE = "Raspberry Pi"
SOFTWARE = "pi-camera"


def _values(metadata, shot_time, manual_gain):
    """The values both formats share. `shot_time` is a timezone-aware datetime."""
    return {
        "datetime": shot_time.strftime("%Y:%m:%d %H:%M:%S"),
        "subsec": f"{shot_time.microsecond:06d}",
        "exposure": (int(metadata["ExposureTime"]), 1_000_000),  # exact, in µs
        # Same convention as picamera2/pidng: total gain x 100, not a calibrated ISO
        "iso": round(metadata["AnalogueGain"] * metadata.get("DigitalGain", 1.0) * 100),
        "program": 1 if manual_gain else 2,  # ExposureProgram: 1 = manual, 2 = normal (auto)
    }


def _author():
    """(tag name, value) for the author tags that are set.

    EXIF text is ASCII, and pidng crashes on anything else: non-ASCII becomes '?'.
    """
    tags = (("Artist", EXIF_ARTIST), ("Copyright", EXIF_COPYRIGHT))
    return [(name, value.encode("ascii", "replace").decode()) for name, value in tags if value]


def jpeg_exif(metadata, shot_time, model, size, manual_gain, manual_wb):
    """piexif dict for the JPEG. Replaces picamera2's own EXIF entirely (its merge is per IFD)."""
    v = _values(metadata, shot_time, manual_gain)
    offset = shot_time.strftime("%z")  # +0100
    zeroth = {
        piexif.ImageIFD.Make: MAKE,
        piexif.ImageIFD.Model: model,
        piexif.ImageIFD.Software: SOFTWARE,
        piexif.ImageIFD.DateTime: v["datetime"],
        piexif.ImageIFD.Orientation: 1,  # sensor is upright, saved photos are never rotated
    }
    for name, value in _author():
        zeroth[getattr(piexif.ImageIFD, name)] = value
    exif = {
        piexif.ExifIFD.ExifVersion: b"0232",
        piexif.ExifIFD.DateTimeOriginal: v["datetime"],
        piexif.ExifIFD.DateTimeDigitized: v["datetime"],
        piexif.ExifIFD.SubSecTimeOriginal: v["subsec"],
        piexif.ExifIFD.OffsetTimeOriginal: f"{offset[:3]}:{offset[3:]}",
        piexif.ExifIFD.ExposureTime: v["exposure"],
        piexif.ExifIFD.ISOSpeedRatings: v["iso"],
        piexif.ExifIFD.ExposureProgram: v["program"],
        piexif.ExifIFD.ExposureMode: 1 if manual_gain else 0,  # 0 = auto, 1 = manual
        piexif.ExifIFD.WhiteBalance: 1 if manual_wb else 0,  # 0 = auto, 1 = manual
        piexif.ExifIFD.ColorSpace: 1,  # sRGB
        piexif.ExifIFD.PixelXDimension: size[0],
        piexif.ExifIFD.PixelYDimension: size[1],
    }
    return {"0th": zeroth, "Exif": exif}


def dng_tags(metadata, shot_time, manual_gain):
    """(pidng Tag, value) pairs added to pidng's own tags (Model, ISO, colour data).

    pidng has no tags for time zone, exposure mode, white balance mode or pixel size: JPEG only.
    Software is left out: pidng always writes its own, and a second one would duplicate the tag.
    """
    v = _values(metadata, shot_time, manual_gain)
    return [
        (Tag.Make, MAKE),
        (Tag.DateTime, v["datetime"]),
        (Tag.DateTimeOriginal, v["datetime"]),
        (Tag.SubsecTimeOriginal, v["subsec"]),
        (Tag.ExposureTime, [list(v["exposure"])]),  # pidng's own rounds to 1/n s
        (Tag.PhotographicSensitivity, [v["iso"]]),
        (Tag.ExposureProgram, [v["program"]]),
    ] + [(getattr(Tag, name), value) for name, value in _author()]
