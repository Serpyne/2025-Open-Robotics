import sys
import os
import asyncio
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

from gpiozero import Button
import time

SWITCH_UPDATE_INTERVAL = 0.1
async def main():
    switch_left = Button(17, pull_up=True)
    switch_right = Button(4, pull_up=True)
    
    while True:
        if switch_left.is_pressed:
            print("DOWN   - CALIBRATE")
        elif switch_right.is_pressed:
            print("UP     - DRIVE")
        else:
            print("MIDDLE - ROBOT OFF")
        await asyncio.sleep(SWITCH_UPDATE_INTERVAL)

if __name__ == "__main__":
    mainloop(main, motors=False, camera=False)