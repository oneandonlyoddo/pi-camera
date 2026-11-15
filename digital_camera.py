
import time
import datetime
from pathlib import Path
from picamera2 import Picamera2, Preview
from pidng.camdefs import Picamera2Camera
from pidng.core import PICAM2DNG
import libcamera
from gpiozero import Button
from settings import (
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
    SETTINGS_FILE,
    TOUCHSCREEN_ENABLED,
    TUNING_FILE,
)
from hud import HUD
import exif
import menu
import presets

# Optional: Import touchscreen support
try:
    from touchscreen import TouchScreen
    TOUCHSCREEN_AVAILABLE = True
except ImportError:
    TOUCHSCREEN_AVAILABLE = False
    print("Note: evdev not available - touchscreen support disabled")


def controls_for(gain, colour_temp, preset="", tuning=None):
    """Picamera2 controls for the web settings and the preset's runtime part. 0 means auto for gain and WB.

    A preset's fixed WB ("wb", Kelvin, as gains from the base `tuning`) applies only while the web WB is auto.
    """
    values = presets.PRESETS.get(preset, {})
    controls = {"AeEnable": True} if gain == 0 else {"AeEnable": False, "AnalogueGain": float(gain)}
    if colour_temp != 0:
        controls.update(AwbEnable=False, ColourTemperature=int(colour_temp))
    elif "wb" in values and tuning:
        controls.update(AwbEnable=False, ColourGains=presets.colour_gains(tuning, values))
    else:
        controls["AwbEnable"] = True
    return controls | presets.controls(values)


# Buffers to fetch per capture format (CAPTURE_FORMATS). ["main", "raw"] is the order tested on the
# device; ["raw", "main"] failed with ENOMEM (docs/SPECS.md). capture_photo saves the DNG first either way (R8).
CAPTURE_STREAMS = {"JPG": ["main"], "RAW": ["raw"], "JPG+RAW": ["main", "raw"]}


def shutter_button(request_capture):
    """The GPIO shutter button wired to `request_capture`, or None if the pin can't be set up.

    An optional button must not take the camera down (pin in use, no GPIO access)."""
    try:
        button = Button(GPIO_BUTTON_PIN, bounce_time=GPIO_DEBOUNCE_TIME)
    except Exception as e:
        print(f"Could not initialize GPIO button on pin {GPIO_BUTTON_PIN}: {e}")
        return None
    button.when_pressed = lambda: request_capture("Shutter button")
    return button


class DigitalCamera:
    """Digital camera controller for Raspberry Pi HQ Camera module."""

    def __init__(self, camera_state, photos_dir=PHOTOS_DIR):
        """
        Initialize the digital camera.

        Args:
            camera_state: Shared CameraState; every shutter source signals through it (R2)
            photos_dir: Directory to save captured photos
        """
        self.camera_state = camera_state
        self.photos_dir = Path(photos_dir)
        self.camera = None
        self.running = False
        self.hud = HUD(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self._last_settings = None  # (gain, colour_temp, preset) last sent to the camera
        self._preset = camera_state.preset  # preset whose tuning the open camera uses
        self._base_tuning = Picamera2.load_tuning_file(TUNING_FILE)  # read once; presets modify copies
        self._last_saved = None  # CameraState.snapshot() last written to SETTINGS_FILE

        self.button = shutter_button(self.request_capture) if GPIO_CONNECTED else None

        # Initialize touchscreen support (optional)
        self.touchscreen = None
        if TOUCHSCREEN_ENABLED and TOUCHSCREEN_AVAILABLE:
            try:
                self.touchscreen = TouchScreen(on_touch_callback=self.on_touch)
            except Exception as e:
                print(f"Could not initialize touchscreen: {e}")
        elif TOUCHSCREEN_ENABLED and not TOUCHSCREEN_AVAILABLE:
            print("Touchscreen enabled in settings but evdev not available")

        self.photos_dir.mkdir(parents=True, exist_ok=True)
        print(f"Photos will be saved to: {self.photos_dir}")

    def setup_camera(self):
        """Open and configure the camera with the tuning for self._preset, start the preview."""
        preset = presets.PRESETS.get(self._preset)
        # Tone curve + WB shift live in the tuning file, which libcamera reads only when the camera opens
        self.camera = Picamera2(tuning=presets.tuning(self._base_tuning, preset) if preset else None)

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

    def on_touch(self, x, y):
        """Touchscreen callback (touch thread): the menu, or the shutter outside it (R2)."""
        if menu.handle_tap(self.camera_state, x * PREVIEW_WIDTH, y * PREVIEW_HEIGHT):
            self.request_capture("Touchscreen")

    def capture_photo(self):
        """Capture one exposure and save it in the chosen resolution and format (JPG and DNG from the same frame)."""
        size = self.camera_state.capture_resolution
        streams = CAPTURE_STREAMS[self.camera_state.capture_format]
        manual_gain = self.camera_state.analogue_gain != 0
        manual_wb = not controls_for(0, self.camera_state.colour_temperature, self.camera_state.preset,
                                     self._base_tuning)["AwbEnable"]
        shot_time = datetime.datetime.now().astimezone()  # one time for filename and EXIF
        timestamp = shot_time.strftime(FILENAME_TIMESTAMP_FORMAT)
        jpg_path = self.photos_dir / f"{FILENAME_PREFIX}_{timestamp}{JPG_EXTENSION}"
        raw_path = jpg_path.with_suffix(RAW_EXTENSION)
        # No transform: saved photos are upright, PREVIEW_ROTATE is for the display only (R8).
        # The raw stream is always configured: its size picks the full-field-of-view sensor mode.
        still_config = self.camera.create_still_configuration(
            main={"size": size},
            raw={"size": size},
            buffer_count=2,  # needed on the Pi Zero (docs/SPECS.md)
        )
        try:
            # Copies the frames, then returns to the preview. Holding the request instead
            # (switch_mode_capture_request_and_stop) fails with ENOMEM on the Pi Zero (docs/SPECS.md).
            buffers, metadata = self.camera.switch_mode_and_capture_buffers(still_config, streams)
            buffers = dict(zip(streams, buffers, strict=True))
            helpers = self.camera.helpers
            model = self.camera.camera_properties.get("Model", "unknown")  # sensor, e.g. "imx477"
            saved = []
            if "raw" in buffers:
                # popped, so its ~18 MB is freed before the JPEG encode needs memory
                self._save_dng(buffers.pop("raw"), metadata, still_config["raw"], raw_path, model,
                               exif.dng_tags(metadata, shot_time, manual_gain))
                saved.append(raw_path.name)
            if "main" in buffers:
                tags = exif.jpeg_exif(metadata, shot_time, model, size, manual_gain, manual_wb)
                helpers.save(helpers.make_image(buffers.pop("main"), still_config["main"]), metadata, str(jpg_path),
                             exif_data=tags)
                saved.insert(0, jpg_path.name)
            print(f"✓ Photo saved: {' + '.join(saved)} ({size[0]}x{size[1]})")
        except Exception as e:
            print(f"✗ Error capturing photo: {e}")

    def _save_dng(self, buffer, metadata, config, path, model, tags):
        """helpers.save_dng() plus our EXIF tags, which it can't take.

        Same steps as picamera2 0.3.39's version, minus PISP_COMP1 decompression (Pi 5 only).
        Opened with "xb": never overwrites an existing file (R11).
        """
        # shortcut: private picamera2 helper (reshapes the raw buffer, no copy); recheck on a picamera2 upgrade
        raw = self.camera.helpers._make_array_shared(buffer, config)
        camera = Picamera2Camera(dict(config), metadata, model)  # copy: pidng writes into the config dict
        for tag, value in tags:
            camera.tags.set(tag, value)
        dng = PICAM2DNG(camera)
        dng.options(compress=0)
        with open(path, "xb") as file:
            dng.convert(raw, file=file)

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

                if self.camera_state.preset != self._preset:
                    # Blocks ~seconds (R6 exception, like a capture); saved below only once the reopen worked
                    self._preset = self.camera_state.preset
                    print(f"Preset {self._preset or 'none'}: reopening the camera with its tuning")
                    self._close_camera()
                    self.setup_camera()
                    self._last_settings = None  # a fresh camera needs every control again

                settings_now = (self.camera_state.analogue_gain, self.camera_state.colour_temperature,
                                self.camera_state.preset)
                if settings_now != self._last_settings:
                    try:
                        self.camera.set_controls(controls_for(*settings_now, self._base_tuning))
                        print(f"Applied gain/colour temperature/preset: {settings_now} (0 = auto)")
                    except Exception as e:
                        print(f"Warning: Failed to apply camera controls: {e}")
                    self._last_settings = settings_now

                snapshot = self.camera_state.snapshot()
                if snapshot != self._last_saved:
                    try:
                        self.camera_state.save(SETTINGS_FILE)
                    except OSError as e:
                        print(f"Warning: could not save settings: {e}")
                    self._last_saved = snapshot

                self.hud.update(self.camera, self.camera_state)
                self.camera_state.wait(HUD_UPDATE_INTERVAL)

        except KeyboardInterrupt:
            print("\nShutting down camera...")
            self.cleanup()

        except Exception as e:
            print(f"Error: {e}")
            self.cleanup()

    def _close_camera(self):
        if self.camera:
            self.camera.stop_preview()
            self.camera.stop()
            self.camera.close()
            self.camera = None

    def cleanup(self):
        """Clean up resources on exit."""
        self.running = False

        # Stop touchscreen monitoring
        if self.touchscreen:
            self.touchscreen.cleanup()

        self._close_camera()

        if self.button:
            self.button.close()

        print("Camera stopped. Goodbye!")
