
import threading
from evdev import InputDevice, ecodes, list_devices
from settings import TOUCH_INVERT_X, TOUCH_INVERT_Y, TOUCH_SWAP_XY


def to_screen(raw_x, raw_y, x_range, y_range, swap=TOUCH_SWAP_XY, invert_x=TOUCH_INVERT_X, invert_y=TOUCH_INVERT_Y):
    """Raw touch values -> (x, y) in 0..1 of the screen as the user sees it. Ranges are (min, max)."""
    x = min(max((raw_x - x_range[0]) / (x_range[1] - x_range[0]), 0.0), 1.0)
    y = min(max((raw_y - y_range[0]) / (y_range[1] - y_range[0]), 0.0), 1.0)
    if swap:
        x, y = y, x
    return (1 - x if invert_x else x), (1 - y if invert_y else y)


class TouchScreen:
    """
    Touchscreen input handler using evdev.
    Calls back once per touch-down with the position.
    """

    def __init__(self, on_touch_callback=None):
        """
        Initialize the touchscreen handler.

        Args:
            on_touch_callback: Called as on_touch_callback(x, y) on touch-down, x and y in 0..1 (see to_screen)
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
            x_codes = (ecodes.ABS_X, ecodes.ABS_MT_POSITION_X)
            y_codes = (ecodes.ABS_Y, ecodes.ABS_MT_POSITION_Y)
            axes = dict(self.device.capabilities()[ecodes.EV_ABS])
            x_info = next(axes[c] for c in x_codes if c in axes)
            y_info = next(axes[c] for c in y_codes if c in axes)
            raw_x, raw_y = x_info.value, y_info.value
            touch_active = False  # trigger only once per touch
            pending = False  # touch-down seen; the position arrives in the same report, so fire at SYN

            for event in self.device.read_loop():
                if not self.running:
                    break

                if event.type == ecodes.EV_KEY and event.code in (ecodes.BTN_TOUCH, ecodes.BTN_LEFT):
                    if event.value == 1 and not touch_active:  # Touch down
                        touch_active = pending = True
                    elif event.value == 0:  # Touch up
                        touch_active = False

                elif event.type == ecodes.EV_ABS:
                    if event.code in x_codes:
                        raw_x = event.value
                    elif event.code in y_codes:
                        raw_y = event.value
                    elif event.code == ecodes.ABS_MT_TRACKING_ID:  # multi-touch devices
                        if event.value != -1 and not touch_active:
                            touch_active = pending = True
                        elif event.value == -1:
                            touch_active = False

                elif event.type == ecodes.EV_SYN and pending:
                    pending = False
                    x, y = to_screen(raw_x, raw_y, (x_info.min, x_info.max), (y_info.min, y_info.max))
                    print(f"Touch raw=({raw_x}, {raw_y}) screen=({x:.2f}, {y:.2f})")  # for calibration
                    if self.on_touch_callback:
                        self.on_touch_callback(x, y)

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
