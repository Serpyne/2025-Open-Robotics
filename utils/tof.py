import time 
from smbus2 import SMBus, i2c_msg

class TOF:
    def __init__(self, address: int, parent: "TOFChain" = None):
        self.address: int = address
        self.parent: None | TOFChain = parent
        
        if self.parent is None:
            self.bus = SMBus(1)
        else:
            self.bus = self.parent.bus
                
    def read(self) -> float:
        data = self.bus.read_i2c_block_data(self.address, 0x10, 5)
        
        sequence = data[0]
        distance = data[1] | (data[2] << 8) | (data[3] << 16) | (data[4] << 24)
        return distance
            
class TOFChain:
    def __init__(self, addresses: list[int], bus_num: int = 1):
        self.addresses: list[int] = addresses
        self.tofs: list[TOF] = [TOF(addr) for addr in self.addresses]
        self.bus: SMBus = SMBus(bus_num)
    def __getitem__(self, i) -> TOF:
        return self.tofs[i]
    def __len__(self) -> int:
        return len(self.tofs)
    def read(self) -> list[float]:
        "returns millimetres"
        return [tof.read() for tof in self.tofs]

if __name__ == "__main__":
    chain = TOFChain([0x55])
    print(f"Number of TOFS: {len(chain)}")
    while True:
        print("Distances: ", chain.read())
        time.sleep(0.1)
