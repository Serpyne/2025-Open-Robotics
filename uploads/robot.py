import sys
import os
import asyncio
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

async def main(motors):
    t = 3
    # motors["dribbler"].set_speed_for(0.5, t)
    [motors[i].set_speed(-0.4) for i in range(4)]
    await asyncio.sleep(t)

if __name__ == "__main__":
    # complete_startup()
    mainloop(main)
