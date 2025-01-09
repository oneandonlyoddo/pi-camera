from gpiozero import Button
from picamera2 import Picamera2
import time

button = Button(26)

with Picamera2() as camera:
    camera.resolution = (4056, 3040)
    camera.framerate = 5
    frame = int(time.time())
    camera.start_preview()
    while True:
        button.wait_for_press()
        camera.capture('/home/pi/Pictures/%03d.jpg' % frame)
        frame += 1