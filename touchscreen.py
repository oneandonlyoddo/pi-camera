
import select
import threading
import time
from evdev import InputDevice, ecodes, list_devices
from settings import TOUCH_INVERT_X, TOUCH_INVERT_Y, TOUCH_LIFT_GRACE, TOUCH_SWAP_XY


class LiftFilter:
    """Merges a lift shorter than `grace` seconds into one touch.

    The resistive panel loses contact for 40-130 ms mid-drag (measured 2026-11-15) and reports
    up + down; without this a drag falls apart into taps. Costs `grace` of latency on a real release.
    """

    def __init__(self, grace):
        self.grace = grace
        self.held = None  # (time, x, y) of a release not yet passed on

    def feed(self, kind, x, y, now):
        """One raw event -> the events to pass on now."""
        if kind == "up":
            self.held = (now, x, y)
            return []
        if kind == "down" and self.held:  # contact back in time: the same touch, moved
            self.held = None
            return [("move", x, y)]
        return [(kind, x, y)]

    def timeout(self, now):
        """Seconds until a held release is due, or None if there is none."""
        return None if self.held is None else max(0.0, self.held[0] + self.grace - now)

    def expire(self, now):
        """The held release, once no new contact came within `grace`."""
        if self.held and now - self.held[0] >= self.grace:
            _t, x, y = self.held
            self.held = None
            return [("up", x, y)]
        return []


def to_screen(raw_x, raw_y, x_range, y_range, swap=TOUCH_SWAP_XY, invert_x=TOUCH_INVERT_X, invert_y=TOUCH_INVERT_Y):
    """Raw touch values -> (x, y) in 0..1 of the screen as the user sees it. Ranges are (min, max)."""
    x = min(max((raw_x - x_range[0]) / (x_range[1] - x_range[0]), 0.0), 1.0)
    y = min(max((raw_y - y_range[0]) / (y_range[1] - y_range[0]), 0.0), 1.0)
    if swap:
        x, y = y, x
    return (1 - x if invert_x else x), (1 - y if invert_y else y)


def _find_device():
    """The first input device with keys and absolute X positions (a touchscreen). Raises OSError if none."""
    for path in list_devices():
        device = InputDevice(path)
        capabilities = device.capabilities(verbose=False)
        abs_codes = [code for code, _info in capabilities.get(ecodes.EV_ABS, [])]
        if ecodes.EV_KEY in capabilities and (ecodes.ABS_X in abs_codes or ecodes.ABS_MT_POSITION_X in abs_codes):
            print(f"Found touchscreen: {device.name} at {device.path}")
            return device
        device.close()
    raise OSError("no touchscreen device found")


class TouchScreen:
    """Touchscreen input via evdev on its own thread.

    Calls on_touch(kind, x, y): kind "down"/"move"/"up", x and y in 0..1 (see to_screen).
    """

    def __init__(self, on_touch):
        self.on_touch = on_touch
        self.device = _find_device()
        self.running = False
        self.thread = None

    def start(self):
        """Start listening for touch events in a background thread."""
        self.running = True
        self.thread = threading.Thread(target=self._event_loop, daemon=True)
        self.thread.start()
        print("Touchscreen monitoring started")

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
            touch_active = False  # one "down" per touch
            pending = []  # "down"/"up" seen; the position arrives in the same report, so send at SYN
            moved = False
            lift = LiftFilter(TOUCH_LIFT_GRACE)

            while self.running:
                # wake when a held release comes due; the 0.5 s cap lets stop() end the thread
                wait = lift.timeout(time.monotonic())
                ready, _w, _x = select.select([self.device.fd], [], [], 0.5 if wait is None else wait)
                for event in (self.device.read() if ready else ()):
                    if event.type == ecodes.EV_KEY and event.code in (ecodes.BTN_TOUCH, ecodes.BTN_LEFT):
                        if event.value == 1 and not touch_active:  # Touch down
                            touch_active = True
                            pending.append("down")
                        elif event.value == 0 and touch_active:  # Touch up
                            touch_active = False
                            pending.append("up")

                    elif event.type == ecodes.EV_ABS:
                        if event.code in x_codes:
                            raw_x, moved = event.value, True
                        elif event.code in y_codes:
                            raw_y, moved = event.value, True
                        elif event.code == ecodes.ABS_MT_TRACKING_ID:  # multi-touch devices
                            if event.value != -1 and not touch_active:
                                touch_active = True
                                pending.append("down")
                            elif event.value == -1 and touch_active:
                                touch_active = False
                                pending.append("up")

                    elif event.type == ecodes.EV_SYN:
                        kinds = pending or (["move"] if moved and touch_active else [])
                        pending, moved = [], False
                        if not kinds:
                            continue
                        x, y = to_screen(raw_x, raw_y, (x_info.min, x_info.max), (y_info.min, y_info.max))
                        if "down" in kinds:
                            print(f"Touch raw=({raw_x}, {raw_y}) screen=({x:.2f}, {y:.2f})")  # for calibration
                        for kind in kinds:
                            self._emit(lift.feed(kind, x, y, time.monotonic()))
                self._emit(lift.expire(time.monotonic()))

        except OSError as e:
            # Device was disconnected or became unavailable
            print(f"Touchscreen device error: {e}")
        except Exception as e:
            print(f"Error in touchscreen event loop: {e}")

    def _emit(self, events):
        for kind, x, y in events:
            self.on_touch(kind, x, y)

    def cleanup(self):
        """Stop the thread (it checks `running` at least every 0.5 s) and close the device."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        try:
            self.device.close()
        except Exception:
            pass
        print("Touchscreen monitoring stopped")
