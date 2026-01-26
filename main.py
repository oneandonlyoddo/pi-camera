#!/usr/bin/env python3

"""
Raspberry Pi Zero Digital Camera
A simple digital camera implementation using the Raspberry Pi HQ Camera module.
Provides fullscreen preview, hardware button trigger, and saves images in JPG and RAW formats.
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