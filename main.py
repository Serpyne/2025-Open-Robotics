import time
import asyncio
from utils.motors_i2c import Motor
from utils.cam import Camera
from threading import Thread
from utils.interface import start_websocket, start_server

motors = {
    0: Motor(address=0x19),
    1: Motor(address=0x1a),
    2: Motor(address=0x1c),
    3: Motor(address=0x1b),
    "dribbler": Motor(address=0x1e)
}
camera = Camera()

async def initialise_event_loop(main_func):
    for index in motors:
        motor = motors[index]
        asyncio.create_task(motor.event_loop())
    main_task = asyncio.create_task(main_func(motors, camera))
    await asyncio.gather(main_task)

def stop_motors():
    for index in motors:
        motor = motors[index]
        motor.set_speed(0)

def mainloop(main_func, loop_forever=True):
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(initialise_event_loop(main_func))
        if loop_forever: loop.run_forever()
    except Exception as e:
        print(e)
        print("Program Halted")
    stop_motors()

def complete_startup(main_func):
    Thread(target=mainloop, args=(main_func,)).start()
    Thread(target=start_websocket).start()
    Thread(target=start_server).start()
