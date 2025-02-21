import time
import asyncio
from motors_i2c import Motor

dribbler_motor = Motor(address=0x1e)
motors = [
    Motor(address=0x19),
    Motor(address=0x1a),
    Motor(address=0x1b),
    Motor(address=0x1c)
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
        loop.create_task(motor.event_loop())
    loop.create_task(main(motors))
    loop.run_forever()


if __name__ == "__main__":
    try:
        initialise_event_loop()
    except KeyboardInterrupt:
        dribbler_motor.set_speed(0)
        for motor in motors:
            motor.set_speed(0)