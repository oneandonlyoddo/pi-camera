#!/usr/bin/env python3
"""
Raspberry Pi Zero Digital Camera
A simple digital camera implementation using the Raspberry Pi HQ Camera module.
Provides fullscreen preview, hardware button trigger, and saves images in JPG and RAW formats.
"""

import time
import datetime
import os
from pathlib import Path
from picamera2 import Picamera2, Preview
from gpiozero import Button
from PIL import Image, ImageDraw, ImageFont
import numpy as np


# Import all settings
from settings import (
    GPIO_BUTTON_PIN,
    GPIO_DEBOUNCE_TIME,
    PHOTOS_DIR,
    FILENAME_PREFIX,
    FILENAME_TIMESTAMP_FORMAT,
    JPG_EXTENSION,
    RAW_EXTENSION,
    PREVIEW_WIDTH,
    PREVIEW_HEIGHT,
    CAPTURE_WIDTH,
    CAPTURE_HEIGHT,
    PREVIEW_WINDOW_WIDTH,
    PREVIEW_WINDOW_HEIGHT,
    PREVIEW_WINDOW_X,
    PREVIEW_WINDOW_Y,
    CAPTURE_PAUSE_DURATION,
    HUD_UPDATE_INTERVAL,
    HUD_FONT_PATH_LARGE,
    HUD_FONT_PATH_SMALL,
    HUD_FONT_SIZE_LARGE,
    HUD_FONT_SIZE_SMALL,
    HUD_DATE_FORMAT,
    HUD_TIME_FORMAT,
    HUD_PADDING,
    HUD_BACKGROUND_PADDING,
    HUD_TEXT_SPACING,
    HUD_COLOR_BACKGROUND,
    HUD_COLOR_TIME_TEXT,
    HUD_COLOR_DATE_TEXT,
    HUD_COLOR_SHADOW,
    HUD_SHADOW_OFFSET
)

class DigitalCamera:
    """Digital camera controller for Raspberry Pi HQ Camera module."""
    
    def __init__(self, button_pin=GPIO_BUTTON_PIN, photos_dir=PHOTOS_DIR):
        """
        Initialize the digital camera.
        
        Args:
            button_pin: GPIO pin number for the shutter button (BCM mode)
            photos_dir: Directory to save captured photos
        """
        self.button = Button(button_pin, bounce_time=GPIO_DEBOUNCE_TIME)
        self.button.when_pressed = self.button_pressed
        self.photos_dir = Path(photos_dir)
        self.camera = None
        self.running = False
        self.overlay = None
        self.preview_size = (PREVIEW_WINDOW_WIDTH, PREVIEW_WINDOW_HEIGHT)
        
        # Create photos directory if it doesn't exist
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        print(f"Photos will be saved to: {self.photos_dir}")
        

        
    def setup_camera(self):
        """Initialize and configure the camera with optimal settings."""
        self.camera = Picamera2()
        
        # Configure camera for high quality still capture
        # Preview config for the live view
        preview_config = self.camera.create_preview_configuration(
            main={"size": (PREVIEW_WIDTH, PREVIEW_HEIGHT)},
            display="main"
        )
        
        # Still config for capturing high-res images
        still_config = self.camera.create_still_configuration(
            main={"size": (CAPTURE_WIDTH, CAPTURE_HEIGHT)},
            raw={"size": (CAPTURE_WIDTH, CAPTURE_HEIGHT)}
        )
        
        # Start with preview configuration
        self.camera.configure(preview_config)
        
       
        # Start the camera with fullscreen preview
        self.camera.start_preview(
            Preview.QTGL,
            x=PREVIEW_WINDOW_X,
            y=PREVIEW_WINDOW_Y,
            width=PREVIEW_WINDOW_WIDTH,
            height=PREVIEW_WINDOW_HEIGHT
        )
        self.camera.start()
        
        # Create initial overlay for HUD
        self.setup_hud()
        
        print("Camera initialized with fullscreen preview")
        
    def button_pressed(self):
        """
        Callback function triggered when shutter button is pressed.
        """
        if self.running:
            print("Shutter button pressed - capturing image...")
            self.capture_photo()
            
    def capture_photo(self):
        """Capture and save a photo in both JPG and RAW formats."""
        try:
            # Generate timestamp-based filename
            timestamp = datetime.datetime.now().strftime(FILENAME_TIMESTAMP_FORMAT)
            jpg_path = self.photos_dir / f"{FILENAME_PREFIX}_{timestamp}{JPG_EXTENSION}"
            raw_path = self.photos_dir / f"{FILENAME_PREFIX}_{timestamp}{RAW_EXTENSION}"
            
            # Switch to still configuration for high-res capture
            still_config = self.camera.create_still_configuration(
                main={"size": (CAPTURE_WIDTH, CAPTURE_HEIGHT)},
                raw={"size": (CAPTURE_WIDTH, CAPTURE_HEIGHT)}
            )
            
            # Capture with both JPG and RAW
            self.camera.switch_mode_and_capture_file(
                still_config,
                str(jpg_path),
                name="main"
            )
            
            # Capture RAW (DNG format)
            self.camera.switch_mode_and_capture_file(
                still_config,
                str(raw_path),
                name="raw"
            )
            
            print(f"✓ Photo saved:")
            print(f"  JPG: {jpg_path}")
            print(f"  RAW: {raw_path}")
            
            # Brief pause before returning to preview
            time.sleep(CAPTURE_PAUSE_DURATION)
            
            # Switch back to preview mode
            preview_config = self.camera.create_preview_configuration(
                main={"size": (PREVIEW_WIDTH, PREVIEW_HEIGHT)},
                display="main"
            )
            self.camera.switch_mode(preview_config)
            
        except Exception as e:
            print(f"✗ Error capturing photo: {e}")
    
    def setup_hud(self):
        """Initialize the HUD overlay for displaying time and date."""
        # Create a transparent overlay image
        overlay_img = Image.new('RGBA', self.preview_size, (0, 0, 0, 0))
        # Picamera2 requires a numpy array for set_overlay
        self.overlay = self.camera.set_overlay(np.asarray(overlay_img))
        print("HUD overlay initialized")
    
    def update_hud(self):
        """Update the HUD overlay with current time and date."""
        # Create a transparent image for the overlay
        overlay_img = Image.new('RGBA', self.preview_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_img)
        
        # Get current date and time
        now = datetime.datetime.now()
        date_str = now.strftime(HUD_DATE_FORMAT)
        time_str = now.strftime(HUD_TIME_FORMAT)
        
        # Try to use a nice font, fall back to default if not available
        try:
            font_large = ImageFont.truetype(HUD_FONT_PATH_LARGE, HUD_FONT_SIZE_LARGE)
            font_small = ImageFont.truetype(HUD_FONT_PATH_SMALL, HUD_FONT_SIZE_SMALL)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Calculate time text dimensions and position (top-right corner)
        time_bbox = draw.textbbox((0, 0), time_str, font=font_large)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = self.preview_size[0] - time_width - HUD_PADDING
        time_y = HUD_PADDING
        
        # Calculate date text dimensions
        date_bbox = draw.textbbox((0, 0), date_str, font=font_small)
        date_width = date_bbox[2] - date_bbox[0]
        date_height = date_bbox[3] - date_bbox[1]
        time_height = time_bbox[3] - time_bbox[1]
        
        # Calculate background rectangle dimensions to fit both time and date
        bg_width = max(time_width, date_width) + (HUD_BACKGROUND_PADDING * 2)
        bg_height = time_height + date_height + (HUD_BACKGROUND_PADDING * 3)
        bg_x = self.preview_size[0] - bg_width - HUD_PADDING + HUD_BACKGROUND_PADDING
        bg_y = HUD_PADDING - HUD_BACKGROUND_PADDING
        
        # Draw semi-transparent background for better readability
        
        draw.rectangle(
            [bg_x, bg_y, bg_x + bg_width, bg_y + bg_height],
            fill=HUD_COLOR_BACKGROUND
        )
        
        # Draw time text with shadow for better visibility
        draw.text(
            (time_x + HUD_SHADOW_OFFSET, time_y + HUD_SHADOW_OFFSET),
            time_str,
            font=font_large,
            fill=HUD_COLOR_SHADOW
        )
        draw.text((time_x, time_y), time_str, font=font_large, fill=HUD_COLOR_TIME_TEXT)
        
        # Draw date (smaller text, below time)
        date_x = self.preview_size[0] - date_width - HUD_PADDING
        date_y = time_y + time_height + HUD_TEXT_SPACING
        draw.text(
            (date_x + HUD_SHADOW_OFFSET, date_y + HUD_SHADOW_OFFSET),
            date_str,
            font=font_small,
            fill=HUD_COLOR_SHADOW
        )
        draw.text((date_x, date_y), date_str, font=font_small, fill=HUD_COLOR_DATE_TEXT)
        
        # Update the overlay
        if self.overlay:
            # Picamera2 requires a numpy array for set_overlay
            self.camera.set_overlay(np.asarray(overlay_img))
            
    def run(self):
        """Start the camera and enter main loop."""
        try:
            print("Starting Raspberry Pi Digital Camera...")
            print("Press Ctrl+C to exit")
            
            self.setup_camera()
            self.running = True
            
            # Keep the program running and update HUD
            while self.running:
                self.update_hud()
                time.sleep(HUD_UPDATE_INTERVAL)
                
        except KeyboardInterrupt:
            print("\nShutting down camera...")
            self.cleanup()
            
        except Exception as e:
            print(f"Error: {e}")
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources on exit."""
        self.running = False
        if self.camera:
            self.camera.stop_preview()
            self.camera.stop()
            self.camera.close()
        self.button.close()
        print("Camera stopped. Goodbye!")


def main():
    """Main entry point for the camera application."""
    camera = DigitalCamera()
    camera.run()


if __name__ == "__main__":
    main()
