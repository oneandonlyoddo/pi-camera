"""Web settings -> Picamera2 controls. Needs picamera2, so it runs on the Pi only."""
import pytest

pytest.importorskip("picamera2")

from digital_camera import controls_for  # noqa: E402


def test_zero_means_auto():
    assert controls_for(0, 0) == {"AeEnable": True, "AwbEnable": True}


def test_manual_values():
    assert controls_for(2.5, 5000) == {
        "AeEnable": False,
        "AnalogueGain": 2.5,
        "AwbEnable": False,
        "ColourTemperature": 5000,
    }


def test_web_strings_and_floats_are_converted():
    controls = controls_for("16", 2000.0)
    assert controls["AnalogueGain"] == 16.0
    assert controls["ColourTemperature"] == 2000 and isinstance(controls["ColourTemperature"], int)
