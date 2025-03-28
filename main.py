from picamera2 import Picamera2, Preview
from libcamera import Transform, controls
from sys import stdin
from termios import TCIOFLUSH, tcflush
from time import strftime
from pynput import keyboard
camera = Picamera2()
loop = True
eTime = 10000
aGain = 1.0
controlNeedsUpdate = False

def on_press(key):
    global loop
    global eTime
    global aGain
    global controlNeedsUpdate

    if key == keyboard.Key.esc:    
        loop = False
        print(loop)
    elif key == keyboard.KeyCode.from_char("s"):
        filename = "./web/static/" + strftime("%Y%m%d-%H%M%S") + '.png'
        camera.switch_mode_and_capture_file("still", filename, format="png", wait=None)
        print(f"\rCaptured {filename} succesfully")
    elif key == keyboard.Key.up:
        eTime += 10
        controlNeedsUpdate = True
    elif key == keyboard.Key.down:
        eTime -= 10
        controlNeedsUpdate = True
    elif key == keyboard.Key.left:
        aGain -= 0.05
        controlNeedsUpdate = True
    elif key == keyboard.Key.right:
        aGain += 0.05
        controlNeedsUpdate = True

listener = keyboard.Listener(on_press=on_press)
listener.start()

WIDTH = 800
HEIGHT = 480
camera.preview_configuration.size = (400, 240)
camera.preview_configuration.format = "YUV420"
camera.still_configuration.size = (1600, 960)
camera.still_configuration.enable_raw()
camera.still_configuration.raw.size = camera.sensor_resolution
camera.set_controls({"ExposureTime": eTime, "AnalogueGain": aGain})
camera.start_preview(Preview.QTGL, x=0, y=0, width=WIDTH, height=HEIGHT)
camera.start()

while loop:
    if controlNeedsUpdate:
        camera.set_controls({"ExposureTime": eTime, "AnalogueGain": aGain})
        controlNeedsUpdate = False
else:
    camera.stop_preview()
    camera.stop()
    camera.close()
    tcflush(stdin, TCIOFLUSH)
