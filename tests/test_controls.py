"""Web settings -> Picamera2 controls. Needs picamera2, so it runs on the Pi only."""
import pytest

pytest.importorskip("picamera2")

from digital_camera import controls_for  # noqa: E402

NEUTRAL = {"Saturation": 1.0, "Sharpness": 1.0, "ExposureValue": 0.0}  # no preset


def test_zero_means_auto():
    assert controls_for(0, 0) == {"AeEnable": True, "AwbEnable": True, **NEUTRAL}


def test_manual_values():
    assert controls_for(2.5, 5000) == {
        "AeEnable": False,
        "AnalogueGain": 2.5,
        "AwbEnable": False,
        "ColourTemperature": 5000,
        **NEUTRAL,
    }


def test_web_strings_and_floats_are_converted():
    controls = controls_for("16", 2000.0)
    assert controls["AnalogueGain"] == 16.0
    assert controls["ColourTemperature"] == 2000 and isinstance(controls["ColourTemperature"], int)


def test_preset_controls_merged(monkeypatch):
    import presets

    monkeypatch.setattr(presets, "PRESETS", {"Mono": {"mono": True, "exposure": 1}})
    controls = controls_for(0, 0, "Mono")
    assert controls["Saturation"] == 0.0 and controls["ExposureValue"] == 1.0 and controls["AeEnable"] is True
    assert controls_for(0, 0, "gone") == controls_for(0, 0)  # unknown name = no preset


def test_preset_fixed_wb_unless_web_wb_is_manual(monkeypatch):
    import presets

    tuning = {"algorithms": [{"rpi.awb": {"ct_curve": [3000, 0.5, 0.5, 6000, 0.25, 1.0]}}]}
    monkeypatch.setattr(presets, "PRESETS", {"Day": {"wb": 4500}})
    controls = controls_for(0, 0, "Day", tuning)
    assert controls["AwbEnable"] is False and "ColourTemperature" not in controls
    assert controls["ColourGains"] == pytest.approx((1 / 0.375, 1 / 0.75))
    web = controls_for(0, 3200, "Day", tuning)  # web value wins
    assert web["ColourTemperature"] == 3200 and "ColourGains" not in web
