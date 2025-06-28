from screen import *
from random import randint
import math

def randomPosition(centre) -> tuple:
    x, y = (randint(0, s.WIDTH - 1), randint(0, s.HEIGHT - 1))
    dx = x - centre[0]
    dy = y - centre[1]
    return int(math.degrees(math.atan2(dy, dx))), int(math.sqrt(dx**2 + dy**2))

def lerp(a, b, step=.1):
    return a + (b - a) * step

target = [0, 0]

def _update():
    global target

    if s.BORDER >= 0:
        s.clear()
    
    s.drawFOV(s.CENTRE, radius=28, direction=s.ballAngle, angle=80, width=1)
    s.drawCircle(s.CENTRE, 5, 0)
    
    s.drawCross((50, 50), radius=2)
    
    ra = math.radians(target[0])
    x = s.CENTRE[0] + target[1] * math.cos(ra)
    y = s.CENTRE[1] + target[1] * math.sin(ra)
    s.drawCircle((x, y), radius=3, width=1)
    
    s.ballAngle = lerp(s.ballAngle, target[0], 0.6)
    s.ballDistance = lerp(s.ballDistance, target[1])
    
    if s.ticks % 7 == 0:
        target = list(randomPosition(s.CENTRE))
    
    s.update()
    
if __name__ == "__main__":
    s = Screen()
    s.start(_update)
