---
paths:
  - "main.py"
  - "digital_camera.py"
  - "touchscreen.py"
  - "hud.py"
  - "shared_state.py"
  - "settings.py"
---

# Camera rules

## R2 · Only the camera loop touches the camera
- Picamera2 is used only from the main thread, inside the camera loop in `DigitalCamera.run()` (plus `setup_camera()` / `cleanup()`).
- Every shutter source (GPIO, touchscreen, web, any future one) only signals a request through `CameraState`. Callbacks never call `capture_photo()`, `set_controls()` or `capture_metadata()`.
- The loop must react to a request promptly: wait on a `threading.Event` with a timeout instead of a fixed `time.sleep()`.
- New shared values go into `CameraState` behind its lock. No other module-level mutable state is shared between threads.

## R8 · Picamera2 conventions
Check API names against the installed version first (`scripts/dev.sh --health` prints it).
- **One exposure per shot:** JPG and DNG come from the same frame, captured once with `switch_mode_and_capture_buffers(still_config, ["main", "raw"])` and saved with `camera.helpers`. Save the DNG first and free its buffer before the JPEG encode. Do not switch to the request-based capture APIs. Why: `docs/SPECS.md` (Still capture API).
- **One place for each config:** preview and still configurations are each built by a single function.
- **Orientation:** apply `PREVIEW_ROTATE` (`libcamera.Transform(hflip=1, vflip=1)`) to the preview configuration and the HUD only, **never to the still configuration**. The preview transform must survive every capture. Why: `docs/SPECS.md` (Enclosure).
- **Keep `buffer_count=2` in the still configuration.** Do not change it without testing on the device. Why: `docs/SPECS.md` (Still capture memory).
- `switch_mode_and_capture_*` already returns to the previous mode. Do not rebuild or re-apply the preview config afterwards.
- **Controls:** send `set_controls()` only when a value changed. `0` means auto: gain → `AeEnable=True`, colour temperature → `AwbEnable=True`.
- **Unique filenames:** a capture must never overwrite an existing file (R11). The filename includes sub-second precision or a counter.
- Release everything in `cleanup()`: camera, GPIO, touchscreen thread. The service stops with SIGINT, so cleanup runs through the `KeyboardInterrupt` path.
