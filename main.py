#!/usr/bin/env python3

"""
Raspberry Pi Zero Digital Camera
A digital camera implementation using the Raspberry Pi HQ Camera module with web interface.
Provides fullscreen preview, hardware button trigger, web-based gallery, and remote control.
Saves images in JPG and RAW formats. Includes a Flask web server for remote access and control.
"""

import threading
import time
from shared_state import CameraState
from web.app import app, init_app

# Import Camera Class (Fallback logic)
try:
    from digital_camera import DigitalCamera
except ImportError:
    print("Warning: Picamera2 dependencies not found. Falling back to WebcamCamera.")
    from webcam_camera import WebcamCamera as DigitalCamera

def run_flask(host='0.0.0.0', port=5000):
    """Run the Flask app in a thread."""
    # Disable reloader to avoid running Main thread logic twice
    app.run(host=host, port=port, debug=False, use_reloader=False)

def main():
    """Main entry point for the camera application."""
    # 1. Initialize Shared State
    camera_state = CameraState()
    
    # 2. Initialize Flask App with State
    init_app(camera_state)
    
    # 3. Start Flask in Background Thread
    print("Starting Web Interface on port 5000...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # 4. Initialize and Run Camera (Main Thread)
    # Pass camera_state to the camera instance
    camera = DigitalCamera(camera_state=camera_state)
    camera.run()

if __name__ == "__main__":
    main()