import sys
import os
import asyncio
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

import gpiod
import time

LED_PIN = 17
switch_middle = 11
switch_up = 13

SWITCH_UPDATE_INTERVAL = 0.1
async def main(motors):
    chip = gpiod.Chip('gpiochip4')
    
    switch_middle = chip.get_line(11)
    switch_up = chip.get_line(13)
    
    switch_middle.request(consumer="switch_middle", type=gpiod.LINE_REQ_DIR_IN)
    switch_up.request(consumer="switch_up", type=gpiod.LINE_REQ_DIR_IN)
    
    def read_position():
        print(switch_middle.get_value(), switch_up.get_value())
        return switch_middle.get_value() + switch_up.get_value()
    
    try:
        while True:
            switch_position = read_position()
            print(switch_position)
            await asyncio.sleep(SWITCH_UPDATE_INTERVAL)
    finally:
        # Release the lines when done
        switch_middle.release()
        switch_up.release()

if __name__ == "__main__":
    mainloop(main)