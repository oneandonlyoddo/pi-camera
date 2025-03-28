from gpiozero import Button
from picamera2 import Picamera2, Preview
from time import strftime, sleep

button = Button(26)
camera = Picamera2()

def capture():
    filename = "./out/" + strftime("%Y%m%d-%H%M%S") + '.png'
    camera.switch_mode_and_capture_file("still", filename, format="png", wait=None)
    print(f"\rCaptured {filename} succesfully")
    sleep(.5)

WIDTH = 1360
HEIGHT = 768
camera.preview_configuration.size = (400, 240)
camera.preview_configuration.format = "YUV420"
camera.still_configuration.size = (1600, 960)
camera.still_configuration.enable_raw()
camera.still_configuration.raw.size = camera.sensor_resolution
camera.start_preview(Preview.DRM, x=0, y=0, width=WIDTH, height=HEIGHT)
camera.start()

while True:
    button.when_released = capture
    
