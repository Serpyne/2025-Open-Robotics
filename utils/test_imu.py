import time
import board
import adafruit_bno08x
from adafruit_bno08x.i2c import BNO08X_I2C

i2c = board.I2C()
bno = BNO08X_I2C(i2c)

# Enable the desired reports
bno.enable_feature(adafruit_bno08x.SH2_ARVR_STABILIZED_RV)
bno.enable_feature(adafruit_bno08x.SH2_GYROSCOPE_CALIBRATED)

# Set the report interval (in microseconds)
report_interval = 100000  # 0.1 seconds

bno.set_feature_report_interval(
    adafruit_bno08x.SH2_ARVR_STABILIZED_RV, report_interval
)
bno.set_feature_report_interval(
    adafruit_bno08x.SH2_GYROSCOPE_CALIBRATED, report_interval
)

while True:
    # Read ARVR Stabilized RV data
    quat_i, quat_j, quat_k, quat_real = bno.quaternion
    print(f"Quaternion: I={quat_i:.3f}, J={quat_j:.3f}, K={quat_k:.3f}, Real={quat_real:.3f}")

    # Read Gyroscope data
    gyro_x, gyro_y, gyro_z = bno.gyro
    print(f"Gyro (rad/s): X={gyro_x:.3f}, Y={gyro_y:.3f}, Z={gyro_z:.3f}")

    time.sleep(0.1)
