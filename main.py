#!/usr/bin/env python3

"""
Raspberry Pi Zero Digital Camera
A digital camera implementation using the Raspberry Pi HQ Camera module with web interface.
Provides fullscreen preview, hardware button trigger, web-based gallery, and remote control.
Saves images in JPG and RAW formats. Includes a Flask web server for remote access and control.
"""

try:
    from digital_camera import DigitalCamera
except ImportError:
    print("Warning: Picamera2 dependencies not found. Falling back to WebcamCamera.")
    from webcam_camera import WebcamCamera as DigitalCamera

def main():
    """Main entry point for the camera application."""
    camera = DigitalCamera()
    camera.run()

if __name__ == "__main__":
    main()