
import threading
from pathlib import Path
from evdev import InputDevice, categorize, ecodes, list_devices

class TouchScreen:
    """
    Touchscreen input handler using evdev.
    Detects touch events and triggers callbacks.
    """

    def __init__(self, on_touch_callback=None):
        """
        Initialize the touchscreen handler.

        Args:
            on_touch_callback: Function to call when screen is touched
        """
        self.device = None
        self.running = False
        self.thread = None
        self.on_touch_callback = on_touch_callback

        # Try to find and initialize touchscreen device
        self._find_touchscreen()

    def _find_touchscreen(self):
        """
        Find the touchscreen input device.
        Looks for devices with touch/absolute positioning capabilities.
        """
        try:
            devices = [InputDevice(path) for path in list_devices()]

            # Look for touchscreen devices
            for device in devices:
                # Check if device has touch capabilities
                capabilities = device.capabilities(verbose=False)

                # Touch devices typically have ABS (absolute positioning) events
                if ecodes.EV_ABS in capabilities and ecodes.EV_KEY in capabilities:
                    # Check for touch-specific events
                    abs_events = capabilities[ecodes.EV_ABS]
                    if any(event[0] in [ecodes.ABS_X, ecodes.ABS_MT_POSITION_X] for event in abs_events):
                        self.device = device
                        print(f"Found touchscreen: {device.name} at {device.path}")
                        return

            print("No touchscreen device found")

        except Exception as e:
            print(f"Error finding touchscreen: {e}")

    def start(self):
        """Start listening for touch events in a background thread."""
        if not self.device:
            print("Cannot start touchscreen: no device available")
            return False

        self.running = True
        self.thread = threading.Thread(target=self._event_loop, daemon=True)
        self.thread.start()
        print("Touchscreen monitoring started")
        return True

    def _event_loop(self):
        """
        Main event loop that monitors touch events.
        Runs in a background thread.
        """
        try:
            # Track touch state to trigger only once per touch
            touch_active = False

            for event in self.device.read_loop():
                if not self.running:
                    break

                # We're interested in BTN_TOUCH or MT (multi-touch) events
                if event.type == ecodes.EV_KEY:
                    if event.code == ecodes.BTN_TOUCH or event.code == ecodes.BTN_LEFT:
                        if event.value == 1 and not touch_active:  # Touch down
                            touch_active = True
                            if self.on_touch_callback:
                                self.on_touch_callback()
                        elif event.value == 0:  # Touch up
                            touch_active = False

                # Alternative: detect MT (multi-touch) slot start
                elif event.type == ecodes.EV_ABS:
                    if event.code == ecodes.ABS_MT_TRACKING_ID:
                        if event.value != -1 and not touch_active:  # New touch
                            touch_active = True
                            if self.on_touch_callback:
                                self.on_touch_callback()
                        elif event.value == -1:  # Touch ended
                            touch_active = False

        except OSError as e:
            # Device was disconnected or became unavailable
            print(f"Touchscreen device error: {e}")
        except Exception as e:
            print(f"Error in touchscreen event loop: {e}")

    def stop(self):
        """Stop listening for touch events."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        print("Touchscreen monitoring stopped")

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        if self.device:
            try:
                self.device.close()
            except Exception:
                pass
