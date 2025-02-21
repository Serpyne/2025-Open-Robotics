import time
import asyncio
from motors_i2c import Motor

if __name__ == "__main__":
    motor = Motor(address=0x1e)

    # try:
    #     firmware_version = motor.getFirmwareVersion()
    #     print(f"Firmware Version: {firmware_version}")

    #     motor.set_speed(90_000_000)
    #     time.sleep(2)
    #     motor.set_speed(0)
    # except KeyboardInterrupt:
    #     print("Exiting")

    motors = [
        Motor("1"),
        Motor("2"),
        Motor("3"),
        Motor("4")
    ]
    async def main(motors):
        motors[0].set_speed_for(1.0, 3.0)
        motors[0].set_speed_for(0.0, 1.0)
        motors[0].set_speed_for(0.5, 2.0)
        motors[1].set_speed_for(1.0, 0.1)
        motors[0].set_speed_for(0.0, 0.1)
        motors[1].set_speed_for(0.0, 0.1)

    def initialise_event_loop():
        loop = asyncio.get_event_loop()
        for motor in motors:
            loop.create_task(motor.update())
        loop.create_task(main(motors))
        loop.run_forever()

    initialise_event_loop()