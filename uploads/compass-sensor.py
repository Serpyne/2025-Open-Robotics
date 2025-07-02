
import sys
import os
import asyncio
import math
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

async def main(compass):
    while True:
        
        print("Orientation in degrees:", compass.read())
        
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    mainloop(main, motors=False, compass=True)
