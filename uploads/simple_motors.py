import sys
import os
import asyncio
import math
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

async def main(motors):
    
    async def drive_in_direction(angle, speed):
        angle *= -1
        angle -= 90
        FL = math.sin(math.radians(35 + angle))
        FR = math.sin(math.radians(35 - angle))

        if abs(FL) >= abs(FR):
            FR = (speed/abs(FL))*FR
            FL = (speed/FL)*abs(FL)
        elif abs(FL) < abs(FR):
            FL = (speed/abs(FR))*FL
            FR = (speed/FR)*abs(FR)
            
        motors[0].set_speed(FL)
        motors[1].set_speed(FR)
        motors[2].set_speed(-FL)
        motors[3].set_speed(-FR)
    
    async def turn_on_dribbler():
        motors['dribbler'].set_speed(-1)
    async def strafe (speed, radius):
        v = 0.19
        motors[0].set_speed(-speed + v)
        motors[1].set_speed(-speed + v)
        motors[2].set_speed(speed + v)
        motors[3].set_speed(speed + v)

    # await turn_on_dribbler()
    await drive_in_direction(0, 0.15)
    await asyncio.sleep(1)
    await drive_in_direction(180, 0.2)
    await asyncio.sleep(0.5)
    await drive_in_direction(180, 0.4)
    await asyncio.sleep(1.0)
    
    angle = 0
    while angle < 180:
        await strafe(0.3, 10)
        await asyncio.sleep(0.1)
        angle += 12.85
    await drive_in_direction(0, 0.2)
        
if __name__ == "__main__":
    mainloop(main)

