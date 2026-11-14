
import threading

class CameraState:
    """
    Thread-safe shared state between the Flask Web App and the Camera Loop.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._shutter = threading.Event()  # an Event, so the camera loop can wait on it
        self._analogue_gain = 0.0  # 0.0 = Auto
        self._colour_temperature = 0  # 0 = Auto

    @property
    def shutter_requested(self):
        return self._shutter.is_set()

    @shutter_requested.setter
    def shutter_requested(self, value):
        if value:
            self._shutter.set()
        else:
            self._shutter.clear()

    def wait_for_shutter(self, timeout):
        """Block until a shutter request arrives or `timeout` seconds pass."""
        self._shutter.wait(timeout)

    @property
    def analogue_gain(self):
        with self._lock:
            return self._analogue_gain

    @analogue_gain.setter
    def analogue_gain(self, value):
        with self._lock:
            self._analogue_gain = value

    @property
    def colour_temperature(self):
        with self._lock:
            return self._colour_temperature

    @colour_temperature.setter
    def colour_temperature(self, value):
        with self._lock:
            self._colour_temperature = value

    def consume_shutter_request(self):
        """
        Atomically check and reset the shutter request.
        Returns True if a request was pending.
        """
        with self._lock:
            if self._shutter.is_set():
                self._shutter.clear()
                return True
            return False
