# Recipe: new shutter trigger / input device

For anything that takes a photo or sends a command from outside the camera loop: buttons, touch, remote, timer.

1. **Hardware facts first:** pin (BCM), wiring, device name. Add them to `docs/SPECS.md` (R9). Check the pin is not already used (`GPIO_BUTTON_PIN`, display, camera).
2. **Module:** for a non-trivial input, a module like `touchscreen.py`: its own daemon thread, a `start()`, and a `cleanup()` that ends the thread and closes the device (R6).
3. **Dependency and missing hardware:** the dependency is an apt package (R1), imported normally. Hardware that may be absent must not take the camera down: the constructor raises, and `DigitalCamera.__init__` catches it in one `try`, prints one line and continues without the trigger (like `TouchScreen` and `shutter_button()`).
4. **Setting:** an enable flag in `settings.py` (like `TOUCHSCREEN_ENABLED`, `GPIO_CONNECTED`).
5. **Callback signals only (R2):** the callback is `lambda: self.request_capture("<Source name>")`, which sets the shutter request in `CameraState` and logs the source. It never calls `capture_photo()` or any Picamera2 method. Debounce in the input layer (gpiozero `bounce_time`, touch-down edge only).
6. **Wire up** in `DigitalCamera`: create in `__init__`, start in `run()`, stop in `cleanup()`.
7. **Tests:** if the input logic has pure parts (event filtering, debounce), test them with fake events.
8. **On device:** `/on-device` verify. `--check` must show the trigger's init line and no errors. The trigger itself needs a person: tell the user exactly what to press/touch and which log line to expect (`scripts/dev.sh --logs` on their side).
9. **Docs:** README (Features, Wiring/Configuration, Troubleshooting if there are permission groups), `docs/FEATURES.md`.
