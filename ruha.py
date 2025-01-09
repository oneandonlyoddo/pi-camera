from gpiozero import Button
from picamera2 import Picamera2, Preview
from time import strftime

button = Button(26)
camera = Picamera2()

def capture():
    filename = strftime("%Y%m%d-%H%M%S") + '.png'
    camera.capture_file(filename, format="png", wait=None)
    print(f"\rCaptured {filename} succesfully")

WIDTH = 800
HEIGHT = 480

camera = Picamera2()
config = camera.create_preview_configuration({"size": (WIDTH, HEIGHT)})
camera.configure(config)
camera.start_preview(Preview.DRM, x=0, y=0, width=WIDTH, height=HEIGHT)
camera.start()


while True:
    button.when_pressed = capture
        