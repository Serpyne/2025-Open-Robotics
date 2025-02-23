import sys
import os
import asyncio
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

async def main(motors):
    t = 10
    motors["dribbler"].set_speed_for(-1.0, t)
    # [motors[i].set_speed_for(-1, t) for i in range(4)]
    [motors[i].set_speed(-0.1) for i in range(4)]

if __name__ == "__main__":
    # complete_startup()
    mainloop(main)
