"""

Main TS robot code; I plan to use this file in competitions.

"""

import sys
import os

parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)

from main import mainloop
from gpiozero import Button
from vector import Vector
import math
import asyncio



class Mode:
    Update = 0x12
    Idle = 0xae
    Calibrate = 0xff
class RobotState:
    position: Vector = Vector()
    velocity: Vector = Vector()
    ball_angle: float = 0
    ball_distance: float = 0
    heading: float = 0
    initial_heading: float = 0
class Utilities:
    def __init__(self, motors=None, camera=None, compass=None, tofs=None):
        self.motors = motors
        self.camera = camera
        self.compass = compass
        self.tofs = tofs
class Robot:
    def __init__(self, motors, camera, compass, tofs):
        
        # self._switch_left:  Button = Button(17, pull_up=True)
        # self._switch_right: Button = Button(4, pull_up=True)
        self.mode: int = Mode.Idle
        
        self.state: RobotState = RobotState()
        self.utils: Utilities = Utilities(motors, camera, compass, tofs)

        self.update_interval: float = 0.1
        
    def calculate_final_direction(self, angle: float, distance: float) -> float:
        
        def angle_poly(x: float) -> float:
            return (-0.00000002124 * pow(x, 5)) + (0.000008243 * pow(x, 4)) -(0.0009351 * pow(x, 3)) +(0.01556 * pow(x, 2)) +(3.204 * x) + 2.928
        def distance_poly(x: float) -> float:
            return (-0.0005 * pow(x, 2)) + (0.015 * x) + 1
        
        is_negative: bool = angle < 0
        
        if is_negative:
            angle = -angle
        
        mapped_angle: float = angle_poly(angle)
        scaled_angle: float = mapped_angle * max(distance_poly(distance), 0)
        
        if is_negative:
            scaled_angle *= -1
            
        return scaled_angle

    async def drive_in_direction(self, angle: float, speed: float):
        # might need to check if ts works for the motor angle setup
        angle *= -1
        angle -= 90
        FL = math.sin(math.radians(35 + angle))
        FR = math.sin(math.radians(35 - angle))

        if abs(FL) >= abs(FR):
            FR = (speed/abs(FL))*FR
            FL = (speed/FL)*abs(FL)
        elif abs(FL) < abs(FR):
            FL = (speed/abs(FR))*FL
            FR = (speed/FR)*abs(FR)
            
        self.utils.motors[0].set_speed(FL)
        self.utils.motors[1].set_speed(FR)
        self.utils.motors[2].set_speed(-FL)
        self.utils.motors[3].set_speed(-FR)
    async def brake(self):
        self.utils.motors[0].set_speed(0)
        self.utils.motors[1].set_speed(0)
        self.utils.motors[2].set_speed(0)
        self.utils.motors[3].set_speed(0)
    
    async def enable_dribbler(self):
        self.utils.motors['dribbler'].set_speed(-1)
    async def stop_dribbler(self):
        self.utils.motors['dribbler'].set_speed(0)
    
    def determine_position(self) -> Vector:
        ...
        return
    
    async def update(self):
        "Logic for the robot gameplay"
        
        if None in [self.utils.camera.angle, self.utils.camera.distance]:
            await asyncio.sleep(0.1)
            await self.brake()
            return
        
        self.state.ball_angle = (270 - math.degrees(self.utils.camera.angle)) % 360 - 180
        self.state.ball_distance = self.utils.camera.distance
        self.state.heading = (self.utils.compass.read() - self.state.initial_heading + 180) % 360 - 180
        self.state.position = self.determine_position() 
        self.state.velocity
        tof_distances: list[float] = self.utils.tofs.read()
        
        ...
        a = self.calculate_final_direction(self.state.ball_angle, self.state.ball_distance)
        await self.drive_in_direction(a, 0.2)

        # print for debugging
        info = {
            "Ball Angle": self.state.ball_angle,
            "Ball Distance": self.state.ball_distance,
            "Heading": self.state.heading,
            "Initial Heading": self.state.initial_heading,
            # "TOF Distances": tof_distances
        }
        max_header = max([len(x) for x in info])
        for header in info:
            line = info[header]
            if type(line) == float: line = round(line, 2)
            print(f"{(header + ' ' * max_header)[:max_header]} | {line}")
        print()

        # Implement BT logic here which will take from bt.json.
        # If bt.json is empty, Use last saved.
        ...
        
    async def idle(self):
        "Robot is not moving or sensing"
        await asyncio.sleep(0.5 - self.update_interval)
        
    async def calibrate(self):
        "Set initial heading"
        self.state.initial_heading = self.utils.compass.read()
        await asyncio.sleep(0.5 - self.update_interval)

    async def start(self):
        
        await self.brake()
        await self.stop_dribbler()
        self.utils.camera.start_event_loop()
        self.utils.camera.show_debug_screen()
        
        while True:
            
            # if self._switch_left.is_pressed:
            #     self.state = Mode.Calibrate
            #     await self.calibrate()
                
            # elif self._switch_right.is_pressed:
            #     self.state = Mode.Update
            #     await self.update()
                
            # else:
            #     self.state = Mode.Idle
            #     await self.idle()
                
            await self.update()
                
            await asyncio.sleep(self.update_interval)



async def main(motors, camera, compass, tofs):
    ts = Robot(motors, camera, compass, tofs)
    await ts.start()
    
if __name__ == "__main__":
    mainloop(main, motors=True, camera=True, screen=False, compass=True, tofs=True)
