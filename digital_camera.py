
import time
import datetime
from pathlib import Path
from picamera2 import Picamera2, Preview
import libcamera
from gpiozero import Button
from settings import *
from hud import HUD

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
        self.hud = HUD(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        
        # Create photos directory if it doesn't exist
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        print(f"Photos will be saved to: {self.photos_dir}")
        
    def setup_camera(self):
        """Initialize and configure the camera with optimal settings."""
        self.camera = Picamera2()
        
        # Start the camera with fullscreen preview
        self.camera.start_preview(
            Preview.DRM,
            x=PREVIEW_WINDOW_X,
            y=PREVIEW_WINDOW_Y,
            width=PREVIEW_WIDTH,
            height=PREVIEW_HEIGHT
        )
        
        # Preview config for the live view
        preview_config = self.camera.create_preview_configuration(main={"size": (PREVIEW_WIDTH, PREVIEW_HEIGHT)})
        preview_config["format"] = "YUV420"
        if PREVIEW_ROTATE:
            preview_config["transform"] = libcamera.Transform(hflip=1, vflip=1)

           # Start with preview configuration
        self.camera.configure(preview_config)
        
        self.camera.start()
        time.sleep(1)
        
        print("Camera initialized with fullscreen preview")
      
    def button_pressed(self):
        """
        Callback function triggered when shutter button is pressed.
        """
        if self.running and GPIO_CONNECTED:
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

    def run(self):
        """Start the camera and enter main loop."""
        try:
            print("Starting Raspberry Pi Digital Camera...")
            print("Press Ctrl+C to exit")
            
            self.setup_camera()
            self.running = True
            
            # Keep the program running and update HUD
            while self.running:
                self.hud.update(self.camera)
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
