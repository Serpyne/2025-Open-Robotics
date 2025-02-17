from motors_i2c import Motor
from smbus2 import SMBus

main_bus = SMBus(1)
motor = Motor(0x6b, main_bus)