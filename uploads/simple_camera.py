import sys
import os
import asyncio
from math import sin, cos, radians
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop
import RPi.GPIO as GPIO

async def main(camera):
    "Main robot event loop"

    """
    camera.start_event_loop()
    camera.distance
    camera.angle
    """

    camera.start_event_loop()

    while True:
        

if __name__ == "__main__":
    mainloop(main)
