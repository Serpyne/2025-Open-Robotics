"""

Time Of Flight (TOF) sensor example.

TOF:
    read(): float
TOFChain:
    len(): int
    read(): list[float]

"""

import os
import sys

parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)

from main import mainloop
import asyncio

async def main(tofs):
    # tofs is a TOFChain "
    
    print(f"Number of TOFS: {len(tofs)}")
    
    while True:
        print(tofs.read())
        await asyncio.sleep(0.1)
    
if __name__ == "__main__":
    mainloop(main, motors=False, tofs=True)