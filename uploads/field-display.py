
import sys
import os
import asyncio
import math
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

class Robot:
    def __init__(self):
        ...
        
    def calculateFinalDirection(self, angle: float, distance: float):
        
        def anglePolynomial(x: float):
            return (-0.00000002124 * pow(x, 5)) + (0.000008243 * pow(x, 4)) -(0.0009351 * pow(x, 3)) +(0.01556 * pow(x, 2)) +(3.204 * x) + 2.928
        def distancePolynomial(x: float):
            return (-0.0005 * pow(x, 2)) + (0.015 * x) + 1
        
        isNegative = angle < 0
        
        if isNegative:
            angle = -angle
        
        mappedAngle = anglePolynomial(angle)
        scaledAngle = mappedAngle * max(distancePolynomial(distance), 0)
        
        if isNegative:
            scaledAngle = -scaledAngle;
            
        return scaledAngle;

async def main(camera):
    camera.start_event_loop()
    ts = Robot()
    
    while True:
        if camera.distance is not None and camera.angle is not None:
            d, a = camera.distance, 90 - math.degrees(camera.angle)
            a *= 1.4
            a = (a + 180) % 360 - 180
            angle = ts.calculateFinalDirection(a, d)
            print(f"Driving in a direction of {angle:.2f} deg.")
            
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    mainloop(main, motors=False, camera=True)
