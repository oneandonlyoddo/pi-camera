from gpiozero import Button
from picamera2 import Picamera2, Preview
from time import strftime

button = Button(26)

with Picamera2() as camera:
    camera_config = camera.create_preview_configuration()
    camera.configure(camera_config)
    camera.start_preview(Preview.QTGL)
    camera.start()
    while True:
        button.wait_for_press()
        filename = strftime("%Y%m%d-%H%M%S") + '.png'
        camera.capture_file(filename, format="png", wait=None)
        print(f"\rCaptured {filename} succesfully")