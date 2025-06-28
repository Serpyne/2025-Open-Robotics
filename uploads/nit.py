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

REFRESH_RATE = 60
BUFFER_TIME = 1 / REFRESH_RATE

async def main(camera, screen):
    camera.start_event_loop()
    
    while True:
        if camera.distance is None or camera.angle is None:
            await asyncio.sleep(0.005)
            continue
        
        screen.ballAngle = 90 - math.degrees(camera.angle)
        screen.ballDistance = camera.distance * 0.5
        movement_direction = calculateFinalDirection(screen.ballAngle, screen.ballDistance)
        
        # Screen Draw Calls and Updates
        
        screen.clear()
        
        screen.drawFOV(screen.CENTRE, radius=28, direction=screen.ballAngle, angle=80, width=1)
        screen.drawCircle(screen.CENTRE, 5, 0)
        
        screen.drawVector(screen.CENTRE, 30, movement_direction)
        
        ra = math.radians(screen.ballAngle)
        x = screen.CENTRE[0] + screen.ballDistance * math.cos(ra)
        y = screen.CENTRE[1] + screen.ballDistance * math.sin(ra)
        screen.drawCircle((x, y), radius=3, width=1)
        
        screen.update()
        
        await asyncio.sleep(BUFFER_TIME)

if __name__ == "__main__":
    mainloop(main, motors=False, camera=True, screen=True)
