import numpy as np
import board
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR
import time

class Compass:
    def __init__(self):
        self.i2c = board.I2C()
        self.bno = BNO08X_I2C(self.i2c)
        time.sleep(0.67)
        self.bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)
    
    def read(self):
        "Get the yaw component of the BNO08x compass sensor"
        quat = self.bno.quaternion
        w, x, y, z = quat[3], quat[0], quat[1], quat[2]
        yaw = np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y**2 + z**2))
        yaw_deg = np.degrees(yaw) % 360
        return yaw_deg
