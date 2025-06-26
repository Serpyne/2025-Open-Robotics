import sys
import os
import asyncio
from math import radians, sin, cos
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

from gpiozero import Button
import time

SWITCH_UPDATE_INTERVAL = 0.1
async def main(motors):
    
    async def turn_on_dribbler():
        motors['dribbler'].set_speed(-1.0)
    async def stopDribbler():
        motors['dribbler'].set_speed(0)
        
    async def drive_in_direction(direction, speed):
        """
        0 deg is straight ahead
        90 deg is right
        ...
        """
        # direction = -1
        direction -= 45
        direction = radians(direction)
        x_speed = speed * sin(direction)
        y_speed = speed * cos(direction)
        motors[0].set_speed(-x_speed)
        motors[1].set_speed(y_speed)
        motors[2].set_speed(x_speed)
        motors[3].set_speed(-y_speed)
    
    switch_left = Button(17, pull_up=True)
    switch_right = Button(4, pull_up=True)
    
    i = 180
    a = 0.1
    while True:
        print(switch_left.is_pressed, switch_right.is_pressed)
        if switch_left.is_pressed:
            # print("DOWN   - CALIBRATE")
            # await turn_on_dribbler()
            # await drive_in_direction(i, 0.3)
            motors[0].set_speed(a)
            motors[1].set_speed(a)
            motors[2].set_speed(a)
            motors[3].set_speed(a)

            await turn_on_dribbler()
        elif switch_right.is_pressed:
            await turn_on_dribbler()
        else:
            # print("MIDDLE - ROBOT OFF")
            await stopDribbler()
            await drive_in_direction(0, 0)
            
        await asyncio.sleep(SWITCH_UPDATE_INTERVAL)

if __name__ == "__main__":
    mainloop(main, motors=True, camera=False)