"""
Rudimentary follow-ball code.
"""

import sys
import os
import asyncio
import math
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

def anglePolynomial(x: float):
    return (-0.00000002124 * pow(x, 5)) + (0.000008243 * pow(x, 4)) -(0.0009351 * pow(x, 3)) +(0.01556 * pow(x, 2)) +(3.204 * x) + 2.928
def distancePolynomial(x: float):
    return (-0.0005 * pow(x, 2)) + (0.015 * x) + 1
def calculateFinalDirection(angle: float, distance: float):
    isNegative = angle < 0

    if isNegative:
        angle = -angle

    mappedAngle = anglePolynomial(angle)
    scaledAngle = mappedAngle * max(distancePolynomial(distance), 0)

    if isNegative:
        scaledAngle = -scaledAngle;
    
    return scaledAngle;

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
            angle = calculateFinalDirection(a, d)
            print(f"Driving in a direction of {angle:.2f} deg.")
            await drive_in_direction(angle, 0.3)
            
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    mainloop(main, motors=True, camera=True)
