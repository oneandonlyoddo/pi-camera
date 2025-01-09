from gpiozero import Button
from picamera2 import Picamera2, Preview
from time import strftime

button = Button(26)

def capture(cam):
    filename = strftime("%Y%m%d-%H%M%S") + '.png'
    cam.capture_file(filename, format="png", wait=None)
    print(f"\rCaptured {filename} succesfully")


with Picamera2() as camera:
    camera_config = camera.create_preview_configuration()
    camera.configure(camera_config)
    camera.start_preview(Preview.QTGL)
    camera.start()
    while True:
        button.when_pressed = capture
        