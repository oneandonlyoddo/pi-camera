"""Presets (Fuji-style recipes) from presets.json: validation and the mapping to Pi camera settings.

Pure functions, no camera. Values are in Fuji recipe steps; settings.py PRESET_*_STEP says what one step does.
Runtime controls (colour, mono, sharpness, exposure) and tuning-file edits (highlight, shadow, WB shift)
both act in the ISP, so the preview and the JPG get them; the DNG never does.
"""
import copy
import json
import math

from settings import (
    COLOUR_TEMP_MAX,
    COLOUR_TEMP_MIN,
    PRESET_COLOR_STEP,
    PRESET_NAME_MAX,
    PRESET_SHARPNESS_STEP,
    PRESET_TONE_STEP,
    PRESET_WB_STEP,
    PRESETS_FILE,
    WB_PRESETS,
)

# key: (low, high); "mono" is a bool
RANGES = {
    "color": (-4, 4), "highlight": (-4, 4), "shadow": (-4, 4), "sharpness": (-4, 4),
    "wb_red": (-9, 9), "wb_blue": (-9, 9), "exposure": (-3, 3),
    "wb": (COLOUR_TEMP_MIN, COLOUR_TEMP_MAX),  # fixed WB in Kelvin; missing = auto. Applied by controls_for()
}


def _valid(name, preset):
    if not isinstance(name, str) or not 0 < len(name) <= PRESET_NAME_MAX or not isinstance(preset, dict):
        return False
    for key, value in preset.items():
        if key == "wb" and isinstance(value, str):
            if value.upper() not in WB_PRESETS:
                return False
        elif key == "mono":
            if not isinstance(value, bool):
                return False
        elif key not in RANGES or isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        elif not RANGES[key][0] <= value <= RANGES[key][1]:  # NaN fails too
            return False
    return True


def load(path):
    """{name: preset} from `path`. A missing or broken file gives {}; invalid presets are skipped."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        print(f"Warning: could not read {path.name}, no presets: {e}")
        return {}
    if not isinstance(data, dict):
        print(f"Warning: {path.name} is not a JSON object, no presets")
        return {}
    presets = {}
    for name, preset in data.items():
        if _valid(name, preset):
            if isinstance(preset.get("wb"), str):  # a WB_PRESETS name -> Kelvin; "auto" = no fixed WB
                preset = {**preset, "wb": WB_PRESETS[preset["wb"].upper()]}
                if not preset["wb"]:
                    del preset["wb"]
            presets[name] = preset
        else:
            print(f"Warning: skipping invalid preset {name!r} in {path.name} (name max {PRESET_NAME_MAX} chars)")
    return presets


PRESETS = load(PRESETS_FILE)


def controls(preset):
    """Picamera2 runtime controls for `preset`; {} gives the neutral values. ExposureValue only acts with auto gain."""
    saturation = 0.0 if preset.get("mono") else max(0.0, 1.0 + PRESET_COLOR_STEP * preset.get("color", 0))
    return {
        "Saturation": saturation,
        "Sharpness": max(0.0, 1.0 + PRESET_SHARPNESS_STEP * preset.get("sharpness", 0)),
        "ExposureValue": float(preset.get("exposure", 0)),
    }


def _algo(tuning, name):
    return next(algo for algo in tuning["algorithms"] if name in algo)[name]


def _tone(y, highlight, shadow):
    """Move output level y (0..1): shadow + darkens the lower half, highlight + brightens the upper half.

    Sine bumps peaking at 0.25 / 0.75. Slope change stays below 1 over the allowed range, so the curve stays monotonic.
    """
    if y < 0.5:
        return y - shadow * PRESET_TONE_STEP * math.sin(2 * math.pi * y)
    return y + highlight * PRESET_TONE_STEP * math.sin(2 * math.pi * (y - 0.5))


def _shift(preset):
    """Red and blue gain factors for the preset's WB shift."""
    return (1 + PRESET_WB_STEP) ** preset.get("wb_red", 0), (1 + PRESET_WB_STEP) ** preset.get("wb_blue", 0)


def colour_gains(base, preset):
    """(red, blue) gains for the preset's fixed WB ("wb", Kelvin) with its WB shift, from the tuning's AWB curve.

    Manual ColourTemperature ignores the tuning's sensitivity_*, so a shifted fixed WB has to be sent as gains.
    """
    curve = _algo(base, "rpi.awb")["ct_curve"]  # flat [ct, r, b, ...]; the gains are 1/r and 1/b
    cts, rs, bs = curve[0::3], curve[1::3], curve[2::3]
    shift_r, shift_b = _shift(preset)
    return shift_r / _interp(preset["wb"], cts, rs), shift_b / _interp(preset["wb"], cts, bs)


def _interp(x, xs, ys):
    """Linear interpolation, clamped at the ends (xs ascending)."""
    if x <= xs[0]:
        return ys[0]
    for x0, x1, y0, y1 in zip(xs, xs[1:], ys, ys[1:], strict=False):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return ys[-1]


def tuning(base, preset):
    """A copy of the libcamera tuning dict `base` (version 2) with the preset's tone curve and WB shift."""
    tuned = copy.deepcopy(base)
    highlight, shadow = preset.get("highlight", 0), preset.get("shadow", 0)
    if highlight or shadow:
        contrast = _algo(tuned, "rpi.contrast")
        curve = contrast["gamma_curve"]  # flat [x0, y0, x1, y1, ...] in 0..65535
        for i in range(1, len(curve), 2):
            curve[i] = round(65535 * min(1.0, max(0.0, _tone(curve[i] / 65535, highlight, shadow))))
    awb = _algo(tuned, "rpi.awb")  # sensitivity_* scale the gains AWB picks, so auto WB stays auto
    shift_r, shift_b = _shift(preset)  # acts on auto WB only; a fixed "wb" gets it via colour_gains()
    awb["sensitivity_r"] *= shift_r
    awb["sensitivity_b"] *= shift_b
    return tuned
