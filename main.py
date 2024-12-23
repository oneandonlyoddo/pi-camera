from picamera2 import Picamera2, Preview
from libcamera import Transform, controls
from pynput import keyboard
import time

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)

def on_press(key):
    if key == keyboard.Key.up:
        pass
    elif key == keyboard.Key.down:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

picam2.start_preview(Preview.QTGL, x=100, y=200, width=800, height=600)
picam2.start()
picam2.title_fields = ["ExposureTime", "AnalogueGain"]

time.sleep(360)