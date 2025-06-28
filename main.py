import time
import asyncio

from utils.motors_i2c import Motor
from utils.cam import Camera
from utils.screen import Screen
from threading import Thread
from utils.interface import start_websocket, start_server

motors_ = {}
camera_ = None
screen_ = None

async def initialise_event_loop(main_func, motors: bool, camera: bool, screen: bool):
    args = []
    if motors:
        for index in motors_:
            motor = motors_[index]
            asyncio.create_task(motor.event_loop())
        args.append(motors_)
    if camera:
        args.append(camera_)
    if screen:
        args.append(screen_)
    main_task = asyncio.create_task(main_func(*args))
    await asyncio.gather(main_task)

def stop_motors():
    for index in motors_:
        motor = motors_[index]
        motor.set_speed(0)

def mainloop(main_func, loop_forever=True, motors=True, camera=False, screen=False):
    global motors_, camera_, screen_

    if motors:
        motors_ = {
            0: Motor(address=0x19),
            1: Motor(address=0x1a),
            3: Motor(address=0x1c),
            2: Motor(address=0x1b),
            "dribbler": Motor(address=0x1e)
        }
    if camera:
        camera_ = Camera()
    if screen:
        screen_ = Screen()

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(initialise_event_loop(main_func, motors, camera, screen))
        if loop_forever: loop.run_forever()
    except Exception as e:
        print(e)
        print("Program Halted")
    stop_motors()

def complete_startup(main_func):
    Thread(target=mainloop, args=(main_func,)).start()
    Thread(target=start_websocket).start()
    Thread(target=start_server).start()
