import sys
import os
import asyncio
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop, stop_motors

async def main(motors):
    stop_motors()

if __name__ == "__main__":
    mainloop(main, loop_forever=False)
