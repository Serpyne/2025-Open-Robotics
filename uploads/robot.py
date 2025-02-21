import sys
import os
parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import *

def main(motors):
    print(motors[0].i2c_address)

if __name__ == "__main__":
    mainloop()