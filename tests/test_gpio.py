"""GPIO shutter button on gpiozero's mock pins: no hardware needed."""
import threading

import pytest
from gpiozero import Device
from gpiozero.pins.mock import MockFactory

from digital_camera import shutter_button  # noqa: E402
from settings import GPIO_BUTTON_PIN


@pytest.fixture(autouse=True)
def mock_pins():
    previous = Device.pin_factory
    Device.pin_factory = MockFactory()
    yield Device.pin_factory
    Device.pin_factory.reset()
    Device.pin_factory = previous


def test_press_requests_capture(mock_pins):
    pressed = threading.Event()
    sources = []
    button = shutter_button(lambda source: (sources.append(source), pressed.set()))
    mock_pins.pin(GPIO_BUTTON_PIN).drive_low()  # pull-up wiring: pressed = low
    assert pressed.wait(1)
    assert sources == ["Shutter button"]
    button.close()


def test_pin_in_use_returns_none_instead_of_crashing(mock_pins):
    first = shutter_button(lambda source: None)
    assert shutter_button(lambda source: None) is None
    first.close()
