#from motors_i2c import Motor
from time import sleep

import smbus2
import struct
import time

class PowerfulBLDCdriver:
    def __init__(self, address, bus_number=1):
        self.i2c_address = address
        self.bus = smbus2.SMBus(bus_number)
        self.QDRformat = 0  # Initialize QDRformat

    def begin(self, address=None, wire=None): #Added to make python compatible
        return True

    def getFirmwareVersion(self):
        try:
            self.bus.write_byte(self.i2c_address, 0x00)
            time.sleep(0.001)  # Added to ensure write completes before requestFrom
            data = self.bus.read_i2c_block_data(self.i2c_address, 0x00, 4)
            version = struct.unpack("<I", bytes(data))[0]  # Little-endian unsigned int
            return version
        except Exception as e:
            print(f"Error getting firmware version: {e}")
            return 0

    def setIqPidConstants(self, kp, ki):
        try:
            data = struct.pack("<ii", kp, ki)  # Little-endian signed ints
            self.bus.write_i2c_block_data(self.i2c_address, 0x40, list(data))
        except Exception as e:
            print(f"Error setting Iq PID constants: {e}")

    def setIdPidConstants(self, kp, ki):
        try:
            data = struct.pack("<ii", kp, ki)  # Little-endian signed ints
            self.bus.write_i2c_block_data(self.i2c_address, 0x41, list(data))
        except Exception as e:
            print(f"Error setting Id PID constants: {e}")

    def setSpeedPidConstants(self, kp, ki, kd):
        try:
            data = struct.pack("<fff", kp, ki, kd)  # Little-endian floats
            self.bus.write_i2c_block_data(self.i2c_address, 0x42, list(data))
        except Exception as e:
            print(f"Error setting Speed PID constants: {e}")

    def setPositionPidConstants(self, kp, ki, kd):
        try:
            data = struct.pack("<fff", kp, ki, kd)  # Little-endian floats
            self.bus.write_i2c_block_data(self.i2c_address, 0x43, list(data))
        except Exception as e:
            print(f"Error setting Position PID constants: {e}")

    def setPositionRegionBoundary(self, boundary):
        try:
            data = struct.pack("<f", boundary)  # Little-endian float
            self.bus.write_i2c_block_data(self.i2c_address, 0x44, list(data))
        except Exception as e:
            print(f"Error setting Position Region Boundary: {e}")

    def configureOperatingModeAndSensor(self, operatingmode, sensortype):
        try:
            self.bus.write_byte_data(self.i2c_address, 0x20, operatingmode + (sensortype << 4))
        except Exception as e:
            print(f"Error configuring Operating Mode and Sensor: {e}")

    def configureCommandMode(self, commandmode):
        try:
            self.bus.write_byte_data(self.i2c_address, 0x21, commandmode)
        except Exception as e:
            print(f"Error configuring Command Mode: {e}")

    def setVoltage(self, voltage):
        try:
            data = struct.pack("<i", voltage)  # Little-endian signed int
            self.bus.write_i2c_block_data(self.i2c_address, 0x10, list(data))
        except Exception as e:
            print(f"Error setting Voltage: {e}")

    def setTorque(self, torque):
        try:
            data = struct.pack("<i", torque)  # Little-endian signed int
            self.bus.write_i2c_block_data(self.i2c_address, 0x11, list(data))
        except Exception as e:
            print(f"Error setting Torque: {e}")

    def setSpeed(self, speed):
        try:
            data = struct.pack("<i", speed)  # Little-endian signed int
            self.bus.write_i2c_block_data(self.i2c_address, 0x12, list(data))

        except Exception as e:
            print(f"Error setting Speed: {e}")

    def setPosition(self, position, elecangle):
        try:
            data = struct.pack("<I", position)  # Little-endian unsigned int
            self.bus.write_i2c_block_data(self.i2c_address, 0x13, list(data))
            self.send8bitvalue(elecangle)  # Assuming this is sent as a separate byte
        except Exception as e:
            print(f"Error setting Position: {e}")

    def setCurrentLimitFOC(self, current):
        try:
            data = struct.pack("<i", current)  # Little-endian signed int
            self.bus.write_i2c_block_data(self.i2c_address, 0x33, list(data))
        except Exception as e:
            print(f"Error setting Current Limit FOC: {e}")

    def setSpeedLimit(self, speed):
        try:
            data = struct.pack("<i", speed)  # Little-endian signed int
            self.bus.write_i2c_block_data(self.i2c_address, 0x34, list(data))
        except Exception as e:
            print(f"Error setting Speed Limit: {e}")

    def clearFaults(self):
        try:
            self.bus.write_byte(self.i2c_address, 0x01)
        except Exception as e:
            print(f"Error clearing faults: {e}")

    def setELECANGLEOFFSET(self, ELECANGLEOFFSET):
        try:
            data = struct.pack("<I", ELECANGLEOFFSET)  # Little-endian unsigned int
            self.bus.write_i2c_block_data(self.i2c_address, 0x30, list(data))
        except Exception as e:
            print(f"Error setting ELECANGLEOFFSET: {e}")

    def setEAOPERSPEED(self, EAOPERSPEED):
        try:
            data = struct.pack("<i", EAOPERSPEED)  # Little-endian signed int
            self.bus.write_i2c_block_data(self.i2c_address, 0x31, list(data))
        except Exception as e:
            print(f"Error setting EAOPERSPEED: {e}")

    def setSINCOSCENTRE(self, SINCOSCENTRE):
        try:
            data = struct.pack("<i", SINCOSCENTRE)  # Little-endian signed int
            self.bus.write_i2c_block_data(self.i2c_address, 0x32, list(data))
        except Exception as e:
            print(f"Error setting SINCOSCENTRE: {e}")

    def setCalibrationOptions(self, voltage, speed, scycles, cycles):
        try:
            data = struct.pack("<Iiii", voltage, speed, scycles, cycles)  # Little-endian unsigned int, signed ints
            self.bus.write_i2c_block_data(self.i2c_address, 0x3A, list(data))
        except Exception as e:
            print(f"Error setting Calibration Options: {e}")

    def startCalibration(self):
        try:
            self.bus.write_i2c_block_data(self.i2c_address, 0x38,[0x01])
            #self.bus.write_byte_data(self.i2c_address, 0x38, 0x01)
        except Exception as e:
            print(f"Error starting Calibration: {e}")

    def stopCalibration(self):
        try:
            self.bus.write_i2c_block_data(self.i2c_address, 0x38, [0x00])
            #self.bus.write_byte_data(self.i2c_address, 0x38, 0x00)
        except Exception as e:
            print(f"Error stopping Calibration: {e}")

    def isCalibrationFinished(self):
        try:
            self.bus.write_byte(self.i2c_address, 0x39)
            time.sleep(0.001) # Added to ensure write completes before read
            data = self.bus.read_i2c_block_data(self.i2c_address, 0x39, 9)

            calibration_state = data[0]
            ELECANGLEOFFSET = struct.unpack("<I", bytes(data[1:5]))[0]
            SINCOSCENTRE = struct.unpack("<i", bytes(data[5:9]))[0]

            if calibration_state == 255:
                return True
            return False
        except Exception as e:
            print(f"Error checking Calibration Finished: {e}")
            return False

    def getCalibrationELECANGLEOFFSET(self):
        try:
            self.bus.write_byte(self.i2c_address, 0x39)
            time.sleep(0.001) # Added to ensure write completes before read
            data = self.bus.read_i2c_block_data(self.i2c_address, 0x39, 9)

            calibration_state = data[0]
            ELECANGLEOFFSET = struct.unpack("<I", bytes(data[1:5]))[0]
            SINCOSCENTRE = struct.unpack("<i", bytes(data[5:9]))[0]

            if calibration_state == 255:
                return ELECANGLEOFFSET
            return 0
        except Exception as e:
            print(f"Error getting Calibration ELECANGLEOFFSET: {e}")
            return 0

    def getCalibrationSINCOSCENTRE(self):
        try:
            self.bus.write_byte(self.i2c_address, 0x39)
            time.sleep(0.001) # Added to ensure write completes before read
            data = self.bus.read_i2c_block_data(self.i2c_address, 0x39, 9)

            calibration_state = data[0]
            ELECANGLEOFFSET = struct.unpack("<I", bytes(data[1:5]))[0]
            SINCOSCENTRE = struct.unpack("<i", bytes(data[5:9]))[0]

            if calibration_state == 255:
                return SINCOSCENTRE
            return 0
        except Exception as e:
            print(f"Error getting Calibration SINCOSCENTRE: {e}")
            return 0

    def setQuickDataReadoutFormat(self, format):
      self.QDRformat = format; #added to prevent errors, even though it does nothing

    def updateQuickDataReadout(self):
        try:
            self.bus.write_byte(self.i2c_address, 0x50)
            time.sleep(0.001) # Added to ensure write completes before read

            data = self.bus.read_i2c_block_data(self.i2c_address,0x50, 10)
            self.QDRposition = struct.unpack("<I", bytes(data[0:4]))[0]
            self.QDRspeed = struct.unpack("<i", bytes(data[4:8]))[0]
            self.QDRERROR1 = data[8]
            self.QDRERROR2 = data[9]
        except Exception as e:
            print(f"Error updating Quick Data Readout: {e}")

    def getPositionQDR(self): return self.QDRposition
    def getSpeedQDR(self): return self.QDRspeed
    def getERROR1QDR(self): return self.QDRERROR1
    def getERROR2QDR(self): return self.QDRERROR2


    # *********************************************************************************************************************************************
    # Private Methods:
    def send32bitvalue(self, value):
        # Helper to send 32-bit values
        try:
            data = struct.pack("<i", value)
            self.bus.write_i2c_block_data(self.i2c_address, 0x00, list(data))  # Dummy register 0x00 - replace if needed
        except Exception as e:
            print(f"Error sending 32-bit value: {e}")

    def send16bitvalue(self, value):
        # Helper to send 16-bit values
        try:
            data = struct.pack("<h", value)
            self.bus.write_i2c_block_data(self.i2c_address, 0x00, list(data))  # Dummy register 0x00 - replace if needed
        except Exception as e:
            print(f"Error sending 16-bit value: {e}")

    def send8bitvalue(self, value):
        # Helper to send 8-bit values
        try:
            self.bus.write_byte(self.i2c_address, value)
        except Exception as e:
            print(f"Error sending 8-bit value: {e}")

    def receive32bitvalue(self):  #Added to make code python compatible.
        try:
            data = self.bus.read_i2c_block_data(self.i2c_address, 0x00, 4)
            value = struct.unpack("<I", bytes(data))[0]
            return value
        except Exception as e:
            print(f"Error receiving 32-bit value: {e}")
            return 0

    def receive16bitvalue(self): #Added to make code python compatible.
        try:
            data = self.bus.read_i2c_block_data(self.i2c_address, 0x00, 2)
            value = struct.unpack("<H", bytes(data))[0]
            return value
        except Exception as e:
            print(f"Error receiving 16-bit value: {e}")
            return 0

    def receive8bitvalue(self): #Added to make code python compatible.
        try:
            return self.bus.read_byte(self.i2c_address)
        except Exception as e:
            print(f"Error receiving 8-bit value: {e}")
            return 0

if __name__ == "__main__":
    MOTOR_ADDRESS = 0x1e

    motor = PowerfulBLDCdriver(MOTOR_ADDRESS)

    try:
        firmware_version = motor.getFirmwareVersion()
        print(f"Firmware Version: {firmware_version}")

        motor.setCurrentLimitFOC(65536 * 2)
        motor.setIdPidConstants(1500, 200)
        motor.setIqPidConstants(1500, 200)
        motor.setSpeedPidConstants(0.04, 0.0004, 0.03)
        motor.setELECANGLEOFFSET(1510395136)
        motor.setSINCOSCENTRE(1251)
        motor.configureOperatingModeAndSensor(3, 1)
        motor.configureCommandMode(12)
        
        motor.setSpeed(40000000)
        time.sleep(2)
        motor.setSpeed(0)
    except KeyboardInterrupt:
        print("Exiting")



sleep(1)
