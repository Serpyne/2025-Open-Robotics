import os
import sys

parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)

from main import mainloop
from vector import Vector
import asyncio
import math

TOF_OFFSET = 18
TOF_RADIUS = 100
TOF_DIRECTIONS = [60, 120, 180, 240, 300]

async def main(compass, tofs):
    await asyncio.sleep(0.5)
    
    orientation: float = 0
    initial_orientation = compass.read()
    
    points: list[Vector] = [Vector(), Vector(), Vector(), Vector(), Vector()]
    
    while True:
        orientation = compass.read() - initial_orientation
        distances = tofs.read()
        
        centroid = Vector()
        
        for i, direction in enumerate(TOF_DIRECTIONS):
            rd = math.radians(direction + orientation)
            d = (distances[i] + TOF_RADIUS - TOF_OFFSET) * 0.1
            points[i].xy[0] = d * math.sin(-rd)
            points[i].xy[1] = d * math.cos(rd)
            centroid += points[i]
        
        centroid /= len(points)
        centroid = Vector(centroid[0] / 182, centroid[1] / 243)
        
        print("DrawPoints", *[[int(p[0]), -int(p.xy[1])] for p in points])
        # print(f"DrawRect {centroid[0] - 0.9} {centroid[1] - 0.9} 1.8 1.8")
            
        await asyncio.sleep(0.1)
    
if __name__ == "__main__":
    mainloop(main, motors=False, tofs=True, compass=True)