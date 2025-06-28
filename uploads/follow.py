import sys
import os
import asyncio
import math
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

a1 = -0.000000021241;
a2 = 0.000008242875;
a3 = -0.000935078305;
a4 = 0.015561992385;
a5 = 3.204488371526;
a6 = 2.928321839083;
def polyFollow(x: float) -> float:
  return a1 * math.pow(x, 5) + a2 * math.pow(x, 4) + a3 * math.pow(x, 3) + a4 * math.pow(x, 2) + a5 * x + a6;

async def main(motors, camera):
    camera.start_event_loop()
    
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

    while True:
        if camera.distance is not None and camera.angle is not None:
            d, a = camera.distance, 90 - math.degrees(camera.angle)
            a *= 1.4
            a = (a + 180) % 360 - 180
            angle = follow_polynomial(a)
            await drive_in_direction(angle, 0.3)
            
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    mainloop(main, motors=True, camera=True)
