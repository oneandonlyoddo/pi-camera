from picamera2 import Picamera2, Preview
from libcamera import Transform, controls
from pynput import keyboard
from time import strftime


cam = Picamera2()
loop = True

def on_press(key):
    if key == keyboard.Key.up:
        global loop
        loop = False
        print(loop)
    elif key == keyboard.Key.down:
        filename = strftime("%Y%m%d-%H%M%S") + '.png'
        cam.capture_file(filename, format="png", wait=None)
        print(f"\rCaptured {filename} succesfully")

listener = keyboard.Listener(on_press=on_press)
listener.start()

cam.start_preview(Preview.QTGL, x=100, y=200, width=800, height=600)
cam.start()
cam.title_fields = ["ExposureTime", "AnalogueGain"]

while loop:
    pass
else:
    cam.stop_preview()
    cam.stop()
    cam.close()
