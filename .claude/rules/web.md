---
paths:
  - "web/**"
---

# Web rules

Read `docs/design/web.md` before changing `web/templates/` or `web/static/`.

## R7 · Treat web input as untrusted
The server has no authentication and is reachable by anyone on the network.
- **Numbers:** validate and range-check every numeric input. Reject NaN/inf. Gain: `0` (auto) or `1.0`–`16.0`. Colour temperature: `0` (auto) or `2000`–`8000`. Return `400` with a message for invalid input; do not silently ignore it.
- **Filenames:** any filename from a URL must be a bare name (`Path(name).name == name`) and resolve inside `DCIM/` (or `DCIM/thumbs/`). Check this before any file is opened or written, not only in `send_from_directory`.
- **No destructive endpoints** (delete, rename, overwrite) without the user's explicit approval for that endpoint.
- **API contract:** any route or payload change updates the README API section in the same change (R9), and the tests in `tests/test_web.py`.
- Web requests run on the Flask thread: they only read files or set `CameraState` (R2), never call the camera.
