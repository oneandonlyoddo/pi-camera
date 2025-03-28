from gpiozero import Button
from picamera2 import Picamera2, Preview
from time import strftime

button = Button(26)
camera = Picamera2()

def capture():
    filename = strftime("%Y%m%d-%H%M%S") + '.png'
    camera.switch_mode_and_capture_file("still", filename, format="png", wait=None)
    print(f"\rCaptured {filename} succesfully")

WIDTH = 800
HEIGHT = 480
camera.preview_configuration.size = (400, 240)
camera.preview_configuration.format = "YUV420"
camera.still_configuration.size = (800, 480)
camera.still_configuration.enable_raw()
camera.still_configuration.raw.size = camera.sensor_resolution

camera.start("preview", show_preview=True)

while True:
    button.when_pressed = capture
        
