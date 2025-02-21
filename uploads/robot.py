import sys
import os
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

async def main(motors):
    for i in range(4):
        motors[i].set_speed_for(1.0, 2)

if __name__ == "__main__":
    mainloop(main)
