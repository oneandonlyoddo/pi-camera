from picamera2 import Picamera2, Preview
from libcamera import Transform, controls
from pynput import keyboard
from time import strftime

camera = Picamera2()
loop = True

def on_press(key):
    if key == keyboard.Key.up:
        global loop
        loop = False
        print(loop)
    elif key == keyboard.Key.down:
        filename = strftime("%Y%m%d-%H%M%S") + '.png'
        camera.switch_mode_and_capture_file("still", filename, format="png", wait=None)
        print(f"\rCaptured {filename} succesfully")

listener = keyboard.Listener(on_press=on_press)
listener.start()

WIDTH = 1360
HEIGHT = 768
camera.preview_configuration.size = (400, 240)
camera.preview_configuration.format = "YUV420"
camera.still_configuration.size = (1600, 960)
camera.still_configuration.enable_raw()
camera.still_configuration.raw.size = camera.sensor_resolution
camera.start_preview(Preview.DRM, x=0, y=0, width=WIDTH, height=HEIGHT)
camera.start()

while loop:
    pass
else:
    cam.stop_preview()
    cam.stop()
    cam.close()
