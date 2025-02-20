from smbus2 import SMBus
import struct

class Motor:
  def __init__(self, address: int):
    self.address: int = address
    self.bus = SMBus(1)

    self.setCurrentLimitFOC(65536 * 2)
    self.setIdPidConstants(1500, 200)
    self.setIqPidConstants(1500, 200)
    self.setSpeedPidConstants(0.04, 0.0004, 0.03)
    self.setELECANGLEOFFSET(1510395136)
    self.setSINCOSCENTRE(1251)
    self.configureOperatingModeAndSensor(3, 1)
    self.configureCommandMode(12)
    self.register = None

  def write(self, byte_value: bytes):
    "Write a byte to I2C"
    self.register = byte_value

  def write_32bit(self, value: int):
    "Write a 32-bit value to I2C"
    if type(value) == float: byte_arr = struct.pack('<f', value)
    else: byte_arr = value.to_bytes(4, 'little')
    self.bus.write_i2c_block_data(self.address, self.register, list(byte_arr))

  def setCurrentLimitFOC(self, current: int):
    self.write(0x33)
    self.write_32bit(current)

  def setIqPidConstants(self, kp: int, ki: int):
    self.write(0x40)
    self.write_32bit(kp)
    self.write_32bit(ki)

  def setIdPidConstants(self, kp: int, ki: int):
    self.write(0x41)
    self.write_32bit(kp)
    self.write_32bit(ki)

  def setSpeedPidConstants(self, kp: float, ki: float, kd: float):
    self.write(0x42)
    self.write_32bit(kp)
    self.write_32bit(ki)
    self.write_32bit(kd)

  def configureOperatingModeAndSensor(self, operating_mode: int, sensor_type: int):
    self.write(0x20)
    self.write(operating_mode + (sensor_type << 4))

  def configureCommandMode(self, command_mode: int):
    self.write(0x21)
    self.write(command_mode)

  def setELECANGLEOFFSET(self, ELEC_ANGLE_OFFSET: int):
    self.write(0x30)
    self.write_32bit(ELEC_ANGLE_OFFSET)

  def setSINCOSCENTRE(self, SIN_COS_CENTRE: int):
    self.write(0x32)
    self.write_32bit(SIN_COS_CENTRE)

  def setSpeed(self, speed: float):
    "Set the speed of brushless motor within a range of -1.0 to 1.0"
    self.write(0x12)
    self.write_32bit(int(90_000_000 * speed))
