
import json
import os
import threading

import presets
from settings import (
    CAPTURE_FORMAT_DEFAULT,
    CAPTURE_FORMATS,
    CAPTURE_RESOLUTIONS,
    COLOUR_TEMP_MAX,
    COLOUR_TEMP_MIN,
    GAIN_MAX,
    GAIN_MIN,
)

PERSISTED = ("analogue_gain", "colour_temperature", "capture_resolution", "capture_format", "preset")


def _locked(name):
    """A property behind CameraState's lock; setting it wakes the camera loop."""
    def get(self):
        with self._lock:
            return getattr(self, name)

    def set_(self, value):
        with self._lock:
            setattr(self, name, value)
        self._wake.set()

    return property(get, set_)


def is_valid(key, value):
    """True if `value` is allowed for the persisted setting `key` (0 = auto for gain/WB)."""
    if key == "capture_resolution":
        return value in CAPTURE_RESOLUTIONS
    if key == "capture_format":
        return value in CAPTURE_FORMATS
    if key == "preset":
        return value == "" or value in presets.PRESETS  # "" = none
    low, high = {"analogue_gain": (GAIN_MIN, GAIN_MAX), "colour_temperature": (COLOUR_TEMP_MIN, COLOUR_TEMP_MAX)}[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value == 0 or low <= value <= high  # NaN fails both


class CameraState:
    """
    Thread-safe shared state between the Flask Web App, the touch menu and the Camera Loop.
    """
    analogue_gain = _locked("_analogue_gain")
    colour_temperature = _locked("_colour_temperature")
    capture_resolution = _locked("_capture_resolution")
    capture_format = _locked("_capture_format")
    menu_open = _locked("_menu_open")
    preset = _locked("_preset")  # name in presets.PRESETS, "" = none

    def __init__(self):
        self._lock = threading.Lock()
        self._shutter = threading.Event()
        self._wake = threading.Event()  # set by a shutter request or a setting change; the loop waits on it
        self._analogue_gain = 0.0  # 0.0 = Auto
        self._colour_temperature = 0  # 0 = Auto
        self._capture_resolution = CAPTURE_RESOLUTIONS[0]
        self._capture_format = CAPTURE_FORMAT_DEFAULT
        self._menu_open = False
        self._preset = ""

    @property
    def shutter_requested(self):
        return self._shutter.is_set()

    @shutter_requested.setter
    def shutter_requested(self, value):
        if value:
            self._shutter.set()
            self._wake.set()
        else:
            self._shutter.clear()

    def wait(self, timeout):
        """Block until a shutter request or setting change arrives or `timeout` seconds pass."""
        self._wake.wait(timeout)
        self._wake.clear()  # the caller re-reads all state after this, so nothing set meanwhile is lost

    def consume_shutter_request(self):
        """
        Atomically check and reset the shutter request.
        Returns True if a request was pending.
        """
        with self._lock:
            if self._shutter.is_set():
                self._shutter.clear()
                return True
            return False

    def snapshot(self):
        """The persisted settings as a dict."""
        return {key: getattr(self, key) for key in PERSISTED}

    def save(self, path):
        """Write the settings to `path` atomically (a crash never leaves half a file)."""
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.snapshot()))
        os.replace(tmp, path)

    def load(self, path):
        """Restore settings from `path`. Missing file: defaults. Invalid values are skipped."""
        try:
            data = json.loads(path.read_text())
        except FileNotFoundError:
            return
        except (OSError, ValueError) as e:
            print(f"Warning: could not read {path.name}, using defaults: {e}")
            return
        if not isinstance(data, dict):
            print(f"Warning: {path.name} is not a JSON object, using defaults")
            return
        for key in PERSISTED:
            if key not in data:
                continue
            value = data[key]
            if key == "capture_resolution" and isinstance(value, list):
                value = tuple(value)  # JSON has no tuples
            if is_valid(key, value):
                setattr(self, key, value)
            else:
                print(f"Warning: ignoring invalid {key}={value!r} in {path.name}")
