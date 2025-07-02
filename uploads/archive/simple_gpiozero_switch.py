import sys
import os
import asyncio
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

from gpiozero import Button
import time

SWITCH_UPDATE_INTERVAL = 0.1
async def main(motors, camera):
    # Works for two way switch rn [Middle wire on gnd, other two on pins 4 and 17]
    # can actually hold the switch in the middle position and both will be false
    switch_left = Button(4, pull_up=True)
    switch_right = Button(17, pull_up=True)

    while True:
        print(f"{switch_left.is_pressed} {switch_right.is_pressed}")
        await asyncio.sleep(SWITCH_UPDATE_INTERVAL)

if __name__ == "__main__":
    mainloop(main)