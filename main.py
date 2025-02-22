import time
import asyncio
from utils.motors_i2c import Motor
from threading import Thread
from utils.interface import start_websocket, start_server

dribbler_motor = Motor(address=0x1e)
motors = [
    Motor(address=0x19),
    Motor(address=0x1a),
    Motor(address=0x1b),
    Motor(address=0x1c)
]

def initialise_event_loop(main_func):
    loop = asyncio.get_event_loop()
    for motor in motors:
        loop.create_task(motor.event_loop())
    loop.create_task(main_func(motors))
    loop.run_forever()

def mainloop(main_func):
    try:
        initialise_event_loop(main_func)
    except KeyboardInterrupt:
        dribbler_motor.set_speed(0)
        for motor in motors:
            motor.set_speed(0)

def complete_startup(main_func):
    Thread(target=mainloop, args=(main_func,)).start()
    Thread(target=start_websocket).start()
    Thread(target=start_server).start()
