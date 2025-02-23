import sys
import os
import asyncio
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

async def main(motors):
    [motors[i].set_speed(1) for i in range(4)]

if __name__ == "__main__":
    mainloop(main)
