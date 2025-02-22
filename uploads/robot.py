import sys
import os
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import *

async def main(motors):
    motors[0].set_speed_for(1.0, 3.0)
    motors[0].set_speed_for(0.0, 1.0)
    motors[0].set_speed_for(0.5, 2.0)
    motors[1].set_speed_for(1.0, 0.1)
    motors[0].set_speed_for(0.0, 0.1)
    motors[1].set_speed_for(0.0, 0.1)

if __name__ == "__main__":
    # complete_startup()
    mainloop(main)