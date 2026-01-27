
import time
import datetime
from pathlib import Path
from picamera2 import Picamera2, Preview
import libcamera
from gpiozero import Button
from PIL import Image
from settings import *
from hud import HUD

class DigitalCamera:
    """Digital camera controller for Raspberry Pi HQ Camera module."""
    

    def __init__(self, button_pin=GPIO_BUTTON_PIN, photos_dir=PHOTOS_DIR, camera_state=None):
        """
        Initialize the digital camera.
        
        Args:
            button_pin: GPIO pin number for the shutter button (BCM mode)
            photos_dir: Directory to save captured photos
            camera_state: Shared CameraState object from the web app
        """
        self.button = Button(button_pin, bounce_time=GPIO_DEBOUNCE_TIME)
        self.button.when_pressed = self.button_pressed
        self.photos_dir = Path(photos_dir)
        self.thumbnails_dir = Path(THUMBNAILS_DIR)
        self.camera = None
        self.running = False
        self.hud = HUD(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.camera_state = camera_state

        # Track last applied settings to avoid unnecessary updates
        self._last_gain = None
        self._last_colour_temp = None

        # Create photos and thumbnails directories if they don't exist
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        print(f"Photos will be saved to: {self.photos_dir}")
        print(f"Thumbnails will be saved to: {self.thumbnails_dir}")
        
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
      
    def generate_thumbnail(self, jpg_path):
        """
        Generate a thumbnail for the given JPG image.

        Args:
            jpg_path: Path to the full-size JPG image
        """
        try:
            # Open the image
            img = Image.open(jpg_path)

            # Create thumbnail (maintains aspect ratio)
            img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)

            # Save thumbnail with same filename in thumbs directory
            thumb_path = self.thumbnails_dir / jpg_path.name
            img.save(thumb_path, "JPEG", quality=THUMBNAIL_QUALITY)

            print(f"  Thumbnail: {thumb_path}")

        except Exception as e:
            print(f"✗ Error generating thumbnail: {e}")

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

            # Generate thumbnail
            self.generate_thumbnail(jpg_path)

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
                # Check for web shutter request
                if self.camera_state and self.camera_state.consume_shutter_request():
                    print("Web shutter request received - capturing image...")
                    self.capture_photo()

                # Apply camera settings if changed
                if self.camera_state:
                    gain = self.camera_state.analogue_gain
                    temp = self.camera_state.colour_temperature

                    # Only apply settings if they've changed
                    controls = {}

                    if gain != self._last_gain:
                        if gain == 0.0:
                            # Auto gain - use AeEnable
                            controls["AeEnable"] = True
                        else:
                            # Manual gain - disable auto exposure and set gain
                            controls["AeEnable"] = False
                            controls["AnalogueGain"] = float(gain)
                        self._last_gain = gain
                        print(f"Applied analogue gain: {'Auto' if gain == 0.0 else gain}")

                    if temp != self._last_colour_temp:
                        if temp == 0:
                            # Auto white balance
                            controls["AwbEnable"] = True
                        else:
                            # Manual white balance with color temperature
                            controls["AwbEnable"] = False
                            controls["ColourGains"] = (temp / 4000.0, temp / 4000.0)  # Simplified color gain calculation
                        self._last_colour_temp = temp
                        print(f"Applied colour temperature: {'Auto' if temp == 0 else str(temp) + 'K'}")

                    # Apply controls if any changed
                    if controls:
                        try:
                            self.camera.set_controls(controls)
                        except Exception as e:
                            print(f"Warning: Failed to apply camera controls: {e}")

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

