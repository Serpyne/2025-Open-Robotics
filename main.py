import time
import asyncio

from utils.motors_i2c import Motor
from utils.cam import Camera
#from utils.screen import Screen
from utils.compass import Compass
from utils.tof import TOFChain, TOF
from threading import Thread
from utils.interface import start_websocket, start_server

motors_ = {}
camera_ = None
screen_ = None
compass_ = None
tofchain_ = None
capture_tof = None

async def initialise_event_loop(main_func, motors: bool, camera: bool, screen: bool, compass: bool, tofs: bool):
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
    if compass:
        args.append(compass_)
    if tofs:
        args.append(tofchain_)
    if capture_tof is not None:
        args.append(capture_tof)
        
    main_task = asyncio.create_task(main_func(*args))
    await asyncio.gather(main_task)

def stop_motors():
    for index in motors_:
        motor = motors_[index]
        motor.set_speed(0)

def mainloop(main_func, loop_forever=True, motors=True, motor_addresses=[0x19, 0x1a, 0x1c, 0x1b], dribbler_address=0x1e,
            camera=False, screen=False, compass=False,
            tofs=False, tof_addresses=[0x50, 0x51, 0x52, 0x53, 0x54], capture_tof_address=None):
    global motors_, camera_, screen_, compass_, tofchain_, capture_tof

    if motors:
        motors_ = {
            0: Motor(address=motor_addresses[0]),
            1: Motor(address=motor_addresses[1]),
            3: Motor(address=motor_addresses[2]),
            2: Motor(address=motor_addresses[3]),
            "dribbler": Motor(address=dribbler_address)
        }
    if camera:
        camera_ = Camera()
    if screen:
        screen_ = Screen()
    if compass:
        compass_ = Compass()
    if tofs:
        tofchain_ = TOFChain(tof_addresses)
    print("capture_tof_address", capture_tof_address)
    if capture_tof_address is not None:
        capture_tof = TOF(capture_tof_address)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(initialise_event_loop(main_func, motors, camera, screen, compass, tofs))
        if loop_forever: loop.run_forever()
    except Exception as e:
        print(e)
        print("Program Halted")
        
    if motors:
        stop_motors()

def complete_startup(main_func):
    Thread(target=mainloop, args=(main_func,)).start()
    Thread(target=start_websocket).start()
    Thread(target=start_server).start()
