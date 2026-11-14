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
- **One exposure per shot:** capture once with `switch_mode_and_capture_request(still_config)`, then `request.save("main", jpg)` and `request.save_dng(dng)`, then `request.release()`. JPG and DNG must come from the same frame.
- **One place for each config:** preview and still configurations are each built by a single function.
- **Orientation:** the camera sensor is mounted upright; the **display** is mounted upside down (`docs/SPECS.md`). `PREVIEW_ROTATE` compensates for the display only: apply it to the preview configuration (`libcamera.Transform(hflip=1, vflip=1)`) and the HUD, **never to the still configuration**. Saved photos are already upright. The preview transform must survive every capture.
- **Keep `buffer_count=2` in the still configuration.** It was added on the device and is needed there. Do not raise or remove it without testing on the device. *Unconfirmed guess at the reason:* memory, since the Pi Zero 2 W (~416 MB usable) may not afford the default buffer count at 4056x3040 with RAW. Replace this line once the real reason is known.
- `switch_mode_and_capture_*` already returns to the previous mode. Do not rebuild or re-apply the preview config afterwards.
- **Controls:** send `set_controls()` only when a value changed. `0` means auto: gain → `AeEnable=True`, colour temperature → `AwbEnable=True`.
- **Unique filenames:** a capture must never overwrite an existing file (R11). The filename includes sub-second precision or a counter.
- Release everything in `cleanup()`: camera, GPIO, touchscreen thread. The service stops with SIGINT, so cleanup runs through the `KeyboardInterrupt` path.
