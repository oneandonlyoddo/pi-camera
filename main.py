from picamera2 import Picamera2, Preview
from libcamera import Transform, controls
from pynput import keyboard
import time


cam = Picamera2()
loop = True

def on_press(key):
    if key == keyboard.Key.up:
        pass
    elif key == keyboard.Key.down:
        pass
    elif key == 's':
        filename = strftime("%Y%m%d-%H%M%S") + '.png'
        cam.capture_file(filename, format="png", wait=None)
        print(f"\rCaptured {filename} succesfully")
    elif key == "q":
        loop = False

listener = keyboard.Listener(on_press=on_press)
listener.start()

cam.start_preview(Preview.QTGL, x=100, y=200, width=800, height=600)
cam.start()
cam.title_fields = ["ExposureTime", "AnalogueGain"]

try:
    while True:
        pass
finally:
    cam.stop_preview()
    cam.stop()
    cam.close()