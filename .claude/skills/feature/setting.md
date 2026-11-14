# Recipe: new runtime camera setting

For values the user changes while the camera runs (like gain and colour temperature). Static configuration goes in `settings.py` only.

1. **Range:** define the valid range once as constants in `settings.py`, like `GAIN_MIN`/`GAIN_MAX` (`0` = auto). Web validation and the UI use these, not their own copies.
2. **State:** add a lock-protected property to `CameraState` in `shared_state.py`, default = auto.
3. **Apply (camera loop only, R2):** extend `controls_for()` in `digital_camera.py` (map auto to the matching `*Enable=True` control) and add the value to the `settings_now` tuple in `DigitalCamera.run()`; controls are sent only when the tuple changes (R8).
   - Look up the libcamera control name and type for the installed picamera2 version (`scripts/dev.sh --health` prints it). Check with `camera.camera_controls` on the Pi if unsure.
   - Mind control interactions: e.g. manual `AnalogueGain`/`ExposureTime` both need `AeEnable=False`.
4. **API (R7):** extend `GET` and `POST /api/settings` in `web/app.py`, validating with `parse_setting(data, key, low, high)` (rejects bools, NaN, inf and out-of-range with `400`).
5. **UI:** add the control to the Settings tab in `web/templates/index.html`, matching `docs/design/web.md`. Pass the range from step 1 through `render_template` in `index()`; `0` shown as "Auto"; use `snapToMin()` on change.
6. **HUD:** if the value should show on the preview, follow `docs/design/hud.md`.
7. **Tests:** `tests/test_web.py` (roundtrip, auto `0`, out-of-range/NaN/bool rejected) and `tests/test_controls.py` (the new controls).
8. **On device:** `/on-device` verify, including step 4 (set the value via curl, shoot, compare with auto, reset).
9. **Docs:** README Configuration + API, `docs/FEATURES.md`.

Settings live in memory and reset to auto on restart. If persistence is wanted, that is a separate design decision. Ask the user.
