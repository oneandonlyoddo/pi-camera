from gpiozero import Button
from picamera2 import Picamera2
from time import strftime

button = Button(26)

with Picamera2() as camera:
    camera.resolution = (4056, 3040)
    camera.framerate = 5
    
    camera.start_preview()
    while True:
        button.wait_for_press()
        filename = strftime("%Y%m%d-%H%M%S") + '.png'
        camera.capture_file(filename, format="png", wait=None)
        print(f"\rCaptured {filename} succesfully")