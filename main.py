#!/usr/bin/env python3

"""
Raspberry Pi Zero Digital Camera
A digital camera implementation using the Raspberry Pi HQ Camera module with web interface.
Provides fullscreen preview, hardware button trigger, web-based gallery, and remote control.
Saves images in JPG and RAW formats. Includes a Flask web server for remote access and control.
"""

import threading
from settings import SETTINGS_FILE
from shared_state import CameraState
from web.app import app, init_app
from digital_camera import DigitalCamera

def run_flask():
    """The web server, on its own thread. No reloader: it would run main() a second time."""
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


def main():
    camera_state = CameraState()
    camera_state.load(SETTINGS_FILE)  # settings from the last run
    init_app(camera_state)

    print("Starting Web Interface on port 5000...")
    threading.Thread(target=run_flask, daemon=True).start()

    DigitalCamera(camera_state).run()  # the camera loop owns the main thread (R2)

if __name__ == "__main__":
    main()