import sys
import os
import asyncio
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop
import RPi.GPIO as GPIO
import time

# Program Constants
MOTOR_UPDATE_INTERVAL = 0.05
SWITCH_UPDATE_INTERVAL = 0.01
switch_position = 1

class position:
    "Toggle-switch position constants"
    SWITCH_UP = 0x00
    SWITCH_MIDDLE = 0x01
    SWITCH_DOWN = 0x02

async def main(motors):
    "Main robot event loop"
    asyncio.create_task(switch_update())
    
    while True:
        match switch_position:
            case position.SWITCH_DOWN:
                motors["dribbler"].set_speed(-1.0)

            case position.SWITCH_MIDDLE:
                [motors[i].set_speed(0) for i in range(4)]
                motors["dribbler"].set_speed(0)

            case position.SWITCH_UP:
                [motors[i].set_speed(-1) for i in range(4)]
            
        await asyncio.sleep(MOTOR_UPDATE_INTERVAL)

async def switch_update():
    "Toggle-switch event loop"
    global switch_position
    GPIO.setmode(GPIO.BOARD)
    switch_middle = 11
    switch_up = 13
    GPIO.setup(switch_middle, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(switch_up, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    def read_position():
        return GPIO.input(switch_middle) + GPIO.input(switch_up)
    
    while True:
        switch_position = read_position()
        await asyncio.sleep(SWITCH_UPDATE_INTERVAL)

if __name__ == "__main__":
    mainloop(main)
