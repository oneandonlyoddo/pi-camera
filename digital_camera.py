
import time
import datetime
from pathlib import Path
from picamera2 import Picamera2, Preview
import libcamera
from gpiozero import Button
from settings import (
    CAPTURE_HEIGHT,
    CAPTURE_WIDTH,
    FILENAME_PREFIX,
    FILENAME_TIMESTAMP_FORMAT,
    GPIO_BUTTON_PIN,
    GPIO_CONNECTED,
    GPIO_DEBOUNCE_TIME,
    HUD_UPDATE_INTERVAL,
    JPG_EXTENSION,
    PHOTOS_DIR,
    PREVIEW_HEIGHT,
    PREVIEW_ROTATE,
    PREVIEW_WIDTH,
    PREVIEW_WINDOW_X,
    PREVIEW_WINDOW_Y,
    RAW_EXTENSION,
    TOUCHSCREEN_ENABLED,
)
from hud import HUD

# Optional: Import touchscreen support
try:
    from touchscreen import TouchScreen
    TOUCHSCREEN_AVAILABLE = True
except ImportError:
    TOUCHSCREEN_AVAILABLE = False
    print("Note: evdev not available - touchscreen support disabled")


def controls_for(gain, colour_temp):
    """Picamera2 controls for the web settings. 0 means auto for both."""
    controls = {"AeEnable": True} if gain == 0 else {"AeEnable": False, "AnalogueGain": float(gain)}
    if colour_temp == 0:
        controls["AwbEnable"] = True
    else:
        controls.update(AwbEnable=False, ColourTemperature=int(colour_temp))
    return controls


class DigitalCamera:
    """Digital camera controller for Raspberry Pi HQ Camera module."""

    def __init__(self, camera_state, button_pin=GPIO_BUTTON_PIN, photos_dir=PHOTOS_DIR):
        """
        Initialize the digital camera.

        Args:
            camera_state: Shared CameraState; every shutter source signals through it (R2)
            button_pin: GPIO pin number for the shutter button (BCM mode)
            photos_dir: Directory to save captured photos
        """
        self.camera_state = camera_state
        self.photos_dir = Path(photos_dir)
        self.camera = None
        self.running = False
        self.hud = HUD(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self._last_settings = None  # (gain, colour_temp) last sent to the camera

        self.button = None
        if GPIO_CONNECTED:
            self.button = Button(button_pin, bounce_time=GPIO_DEBOUNCE_TIME)
            self.button.when_pressed = lambda: self.request_capture("Shutter button")

        # Initialize touchscreen support (optional)
        self.touchscreen = None
        if TOUCHSCREEN_ENABLED and TOUCHSCREEN_AVAILABLE:
            try:
                self.touchscreen = TouchScreen(on_touch_callback=lambda: self.request_capture("Touchscreen"))
            except Exception as e:
                print(f"Could not initialize touchscreen: {e}")
        elif TOUCHSCREEN_ENABLED and not TOUCHSCREEN_AVAILABLE:
            print("Touchscreen enabled in settings but evdev not available")

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

        # The only preview config; captures return to it, rotation included (R8)
        preview_config = self.camera.create_preview_configuration(main={"size": (PREVIEW_WIDTH, PREVIEW_HEIGHT)})
        if PREVIEW_ROTATE:
            preview_config["transform"] = libcamera.Transform(hflip=1, vflip=1)
        self.camera.configure(preview_config)

        self.camera.start()
        time.sleep(1)

        print("Camera initialized with fullscreen preview")

    def request_capture(self, source):
        """Shutter callback for input threads: only signals the camera loop (R2)."""
        print(f"{source} - capture requested")
        self.camera_state.shutter_requested = True

    def capture_photo(self):
        """Capture one exposure and save it as JPG and DNG (same frame)."""
        timestamp = datetime.datetime.now().strftime(FILENAME_TIMESTAMP_FORMAT)
        jpg_path = self.photos_dir / f"{FILENAME_PREFIX}_{timestamp}{JPG_EXTENSION}"
        raw_path = jpg_path.with_suffix(RAW_EXTENSION)
        # No transform: saved photos are upright, PREVIEW_ROTATE is for the display only (R8)
        still_config = self.camera.create_still_configuration(
            main={"size": (CAPTURE_WIDTH, CAPTURE_HEIGHT)},
            raw={"size": (CAPTURE_WIDTH, CAPTURE_HEIGHT)},
            buffer_count=2,  # needed on the Pi Zero (docs/SPECS.md)
        )
        try:
            # Copies both frames, then returns to the preview. Holding the request instead
            # (switch_mode_capture_request_and_stop) fails with ENOMEM on the Pi Zero (docs/SPECS.md).
            (main, raw), metadata = self.camera.switch_mode_and_capture_buffers(still_config, ["main", "raw"])
            helpers = self.camera.helpers
            helpers.save_dng(raw, metadata, still_config["raw"], str(raw_path))
            del raw  # free ~18 MB before the JPEG encode needs memory
            helpers.save(helpers.make_image(main, still_config["main"]), metadata, str(jpg_path))
            print(f"✓ Photo saved: {jpg_path.name} + {raw_path.name}")
        except Exception as e:
            print(f"✗ Error capturing photo: {e}")

    def run(self):
        """Start the camera and enter main loop."""
        try:
            print("Starting Raspberry Pi Digital Camera...")
            print("Press Ctrl+C to exit")

            self.setup_camera()
            self.running = True

            # Start touchscreen monitoring if available
            if self.touchscreen:
                self.touchscreen.start()

            while self.running:
                if self.camera_state.consume_shutter_request():
                    print("Capturing image...")
                    self.capture_photo()
                    self.camera_state.consume_shutter_request()  # drop taps made during the capture

                settings_now = (self.camera_state.analogue_gain, self.camera_state.colour_temperature)
                if settings_now != self._last_settings:
                    try:
                        self.camera.set_controls(controls_for(*settings_now))
                        print(f"Applied gain/colour temperature: {settings_now} (0 = auto)")
                    except Exception as e:
                        print(f"Warning: Failed to apply camera controls: {e}")
                    self._last_settings = settings_now

                self.hud.update(self.camera)
                self.camera_state.wait_for_shutter(HUD_UPDATE_INTERVAL)

        except KeyboardInterrupt:
            print("\nShutting down camera...")
            self.cleanup()

        except Exception as e:
            print(f"Error: {e}")
            self.cleanup()

    def cleanup(self):
        """Clean up resources on exit."""
        self.running = False

        # Stop touchscreen monitoring
        if self.touchscreen:
            self.touchscreen.cleanup()

        # Stop camera
        if self.camera:
            self.camera.stop_preview()
            self.camera.stop()
            self.camera.close()

        if self.button:
            self.button.close()

        print("Camera stopped. Goodbye!")
