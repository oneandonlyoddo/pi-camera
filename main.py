#!/usr/bin/env python3

"""
Raspberry Pi Zero Digital Camera
A simple digital camera implementation using the Raspberry Pi HQ Camera module.
Provides fullscreen preview, hardware button trigger, and saves images in JPG and RAW formats.
"""

from digital_camera import DigitalCamera

def main():
    """Main entry point for the camera application."""
    camera = DigitalCamera()
    camera.run()

if __name__ == "__main__":
    main()