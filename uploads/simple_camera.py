import sys
import os
import asyncio
import math
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

import cv2

async def main(motors, camera):
    # Begins camera stream and starts camera image processing
    camera.start_event_loop()
    
    while True:
        print(camera.distance, camera.angle)
        await asyncio.sleep(0.1)
        
        # to view camera stream on pi5
        if camera.frame is not None:
            cv2.imshow("RPI5", camera.frame)
            cv2.waitKey(1)
    
if __name__ == "__main__":
    mainloop(main)

