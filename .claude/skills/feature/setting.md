# Recipe: new runtime camera setting

For values the user changes while the camera runs (like gain and colour temperature). Static configuration goes in `settings.py` only.

1. **Range:** define the valid range and the "auto" value once as constants in `settings.py` (e.g. `EXPOSURE_MIN_US`, `EXPOSURE_MAX_US`; `0` = auto). Web validation and the UI use these, not their own copies.
2. **State:** add a lock-protected property to `CameraState` in `shared_state.py`, default = auto.
3. **Apply (camera loop only, R2):** in `DigitalCamera.run()`, compare with a `_last_<name>` value and call `set_controls()` only on change (R8). Map auto to the matching `*Enable=True` control.
   - Look up the libcamera control name and type for the installed picamera2 version (`scripts/dev.sh --health` prints it). Check with `camera.camera_controls` on the Pi if unsure.
   - Mind control interactions: e.g. manual `AnalogueGain`/`ExposureTime` both need `AeEnable=False`.
4. **API (R7):** extend `GET` and `POST /api/settings` in `web/app.py`. Validate type and range, reject NaN/inf, return `400` with a message on invalid input.
5. **UI:** add the control to the Settings tab in `web/templates/index.html`, matching `docs/design/web.md`. Range from step 1; `0` shown as "Auto".
6. **HUD:** if the value should show on the preview, follow `docs/design/hud.md`.
7. **Tests** in `tests/test_web.py`: roundtrip, auto (`0`), and out-of-range/NaN rejected.
8. **On device:** `/on-device` verify, including step 5 (set the value via curl, shoot, compare with auto, reset).
9. **Docs:** README Configuration + API, `docs/FEATURES.md`.

Settings live in memory and reset to auto on restart. If persistence is wanted, that is a separate design decision. Ask the user.
