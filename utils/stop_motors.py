import sys
import os
import asyncio
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop, stop_motors

async def main(motors):
    print("Stopped Motors")
    stop_motors()

print("stop_motors.py run")
if __name__ == "__main__":
    print("1")
    mainloop(main, loop_forever=False)
