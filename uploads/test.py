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

from utils.motors_i2c import Motor
from utils.cam import Camera
from utils.compass import Compass
from utils.tof import TOFChain

import pygame
from pygame.locals import *
from threading import Thread
from scipy.optimize import minimize
import numpy as np

from time import perf_counter


PW, PH = 100 * 3, 145 * 3
FW, FH = 115 * 3, 159 * 3
# PW, PH = 158 * 3, 219 * 3
# FW, FH = 182 * 3, 243 * 3
SW, SH = FW + 400, FH + 400
PI = math.pi

TOF_OFFSET = 18
TOF_RADIUS = 100
TOF_DIRECTIONS = [60, 120, 180, 240, 300]



def normaliseAngle(x: float) -> float:
    return (x + 180) % 360 - 180

class Mode:
    Update = 0x12
    Idle = 0xae
    Calibrate = 0xff
class RobotState:
    position: Vector = Vector()
    true_position: Vector = Vector()
    velocity: Vector = Vector()
    ball_angle: float = 0
    ball_distance: float = 0
    heading: float = 0
    initial_heading: float = 0
    tof_distances: list[float] = []
class Utilities:
    def __init__(self, motors=None, camera=None, compass=None, tofs=None):
        self.motors = motors
        self.camera = camera
        self.compass = compass
        self.tofs = tofs
class Robot:
    def __init__(self, motors, camera, compass, tofs):
        
        self.mode: int = Mode.Update
        
        self.state: RobotState = RobotState()
        self.utils: Utilities = Utilities(motors, camera, compass, tofs)

        self.update_interval: float = 0.05
        
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
        if self.state.tof_distances is None: return
        if len(self.state.tof_distances) == 0: return
    
        points = []
        for i, distance in enumerate(self.state.tof_distances):
            a = math.radians(TOF_DIRECTIONS[i] + self.state.heading)
            d = distance + TOF_RADIUS - TOF_OFFSET
            point = [d * math.sin(-a), d * math.cos(a)]
            pygame.draw.circle(self.screen, (255, 255, 0), (point[0] / 10 + self.centre[0], SH - (point[1] / 10 + self.centre[1])), 3)
            points.append(point)
        points = np.array(points)
    
        w, h = 1150, 1590
        # w, h = 1820, 2430
        
        def point_to_aabb_perimeter_dist(px: float, py: float, x0: float, y0: float, w: float, h: float) -> float:
            cx = np.clip(px, x0, x0 + w)
            cy = np.clip(py, y0, y0 + h)
            if x0 < px < x0 + w and y0 < py < y0 + h:
                dist_x = min(px - x0, x0 + w - px)
                dist_y = min(py - y0, y0 + h - py)
                return min(dist_x, dist_y)
            return np.hypot(px - cx, py - cy)
        
        def total_distance(params: tuple[float, float], points: list[tuple], w: float, h: float) -> float:
            x0, y0 = params
            return sum(point_to_aabb_perimeter_dist(px, py, x0, y0, w, h) for px, py in points)
            
        centroid = points.mean(axis = 0)
        init_x0 = centroid[0] - w / 2
        init_y0 = centroid[1] - h / 2
        res = minimize(total_distance, [init_x0, init_y0], args = (points, w, h))
        best_x0, best_y0 = res.x
        
        return Vector(float(best_x0 / w), float(best_y0 / h))
    
    async def update(self):
        "Logic for the robot gameplay"
        
        self.state.tof_distances: list[float] = self.utils.tofs.read()
        self.state.heading: float = normaliseAngle(self.utils.compass.read() - self.state.initial_heading)

        # start = perf_counter()
        self.state.position = self.determine_position()
        # print(f"{perf_counter() - start:.3f}")
        
        points = [Vector(), Vector(), Vector(), Vector(), Vector()]
        for i, direction in enumerate(TOF_DIRECTIONS):
            rd = math.radians(direction + self.state.heading)
            d = (self.state.tof_distances[i] + TOF_RADIUS - TOF_OFFSET) * 0.1 * 3
            points[i].xy[0] = d * math.sin(-rd)
            points[i].xy[1] = d * math.cos(rd)
        
        info = {
            "TOF Distances": [int(x) for x in self.state.tof_distances],
            "Heading": int(self.state.heading),
            "Points": [p.int() for p in points],
            "Position": self.state.position
        }
        max_header = max([len(x) for x in info])
        for header in info:
            line = info[header]
            if type(line) == float: line = round(line, 2)
            print(f"{(header + ' ' * max_header)[:max_header]} | {line}")
        print()
        
        return info

    async def idle(self):
        "Robot is not moving or sensing"
        await asyncio.sleep(0.5 - self.update_interval)
        
    async def calibrate(self):
        "Set initial heading"
        self.state.initial_heading = self.utils.compass.read()
        await asyncio.sleep(0.5 - self.update_interval)

    def drawField(self):
        pygame.draw.rect(self.screen, (100, 200, 100), (200, 200, FW, FH))
        pygame.draw.rect(self.screen, (210, 210, 210), (self.centre[0] - PW//2, self.centre[1] - PH//2, PW, PH), 5)
        pygame.draw.circle(self.screen, (20, 20, 20), self.centre.xy, 3 * 25, 3)
        for point in [(-39, -64.5), (39, -64.5), (-39, 64.5), (39, 64.5)]:
            pygame.draw.circle(self.screen, (20, 20, 20), (self.centre[0] + point[0] * 3, self.centre[1] + point[1] * 3), 4)
        y1 = self.centre[1] + PH // 2
        x1 = self.centre[0] - 40 * 3
        x2 = self.centre[0] + 40 * 3
        pygame.draw.line(self.screen, (210, 210, 210), (x1, y1), (x1, y1 - 10 * 3), 3)
        pygame.draw.line(self.screen, (210, 210, 210), (x2, y1), (x2, y1 - 10 * 3), 3)
        pygame.draw.line(self.screen, (210, 210, 210), (x1 + 15*3, y1 - 25 * 3), (x2 - 15*3, y1 - 25 * 3), 3)
        pygame.draw.arc(self.screen, (210, 210, 210), (x1, y1 - 25 * 3, 30 * 3, 30 * 3), PI/2, PI, 3)
        pygame.draw.arc(self.screen, (210, 210, 210), (x2 - 30 * 3, y1 - 25 * 3, 30 * 3, 30 * 3), 0, PI/2, 3)
        y2 = self.centre[1] - PH // 2
        pygame.draw.line(self.screen, (210, 210, 210), (x1, y2), (x1, y2 + 10 * 3), 3)
        pygame.draw.line(self.screen, (210, 210, 210), (x2, y2), (x2, y2 + 10 * 3), 3)
        pygame.draw.line(self.screen, (210, 210, 210), (x1 + 15*3, y2 + 25 * 3), (x2 - 15*3, y2 + 25 * 3), 3)
        pygame.draw.arc(self.screen, (210, 210, 210), (x1, y2 - 5 * 3, 30 * 3, 30 * 3), PI, 3*PI/2, 3)
        pygame.draw.arc(self.screen, (210, 210, 210), (x2 - 30 * 3, y2 - 5 * 3, 30 * 3, 30 * 3), 3*PI/2, 0, 3)

    async def tofTest(self):
        info = await self.update()
        
        if self.state.position is not None:
            pos = self.state.position
            pos.xy[0] *= FW
            pos.xy[1] *= FH
            print(pos)
            draw = Vector(-FW//2 - pos[0] + self.centre[0], SH - (-FH//2 - pos[1] + self.centre[1]))
            pos += self.centre
            pygame.draw.circle(self.screen, (210, 210, 210), draw.int().xy, 3 * 10)
            if self.state.heading is not None:
                rd = -math.radians(self.state.heading)
                dp = Vector(50 * math.sin(rd), -50 * math.cos(rd))
                pygame.draw.line(self.screen, (255, 20, 20), draw.xy, (draw + dp).xy, 3)
                
            pygame.draw.rect(self.screen, (0, 0, 255), (pos[0], SH - pos[1] - FH, FW, FH), 3)

            pygame.draw.circle(self.screen, (255, 0, 0), self.centre.xy, 3)
            points = info["Points"]
            for point in points:
                point.xy[1] *= -1
                point += self.centre
                pygame.draw.circle(self.screen, (255, 255, 255), point.xy, 3)
            
            
        
    async def start(self):
        
        self.screen = pygame.display.set_mode((SW, SH))
        
        await asyncio.sleep(0.5)
        self.state.initial_heading = self.utils.compass.read()
        await asyncio.sleep(0.5)
        
        self.centre = Vector(SW // 2, SH // 2).int()
        
        while True:            
            await asyncio.sleep(self.update_interval)

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
            
            self.screen.fill("#131313")
            self.drawField()
            
            await self.tofTest()
            
            # pygame.draw.line(self.screen, (self.))
            
            pygame.display.flip()


async def main(compass, tofs):
    global ts
    ts = Robot(None, None, compass, tofs)
    await ts.start()
    
TOF_ADDRESSES = [0x50, 0x51, 0x52, 0x53, 0x54]
async def initialise_event_loop(main_func, motors=False, camera=False, compass=True, tofs=True):
    args = []
    motors_ = {}
    if motors:
        for index in motors_:
            motor = motors_[index]
            asyncio.create_task(motor.event_loop())
        args.append(motors_)
    if camera:
        args.append(Camera())
    if compass:
        args.append(Compass())
    if tofs:
        args.append(TOFChain(TOF_ADDRESSES))

    main_task = asyncio.create_task(main_func(*args))
    await asyncio.gather(main_task)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(initialise_event_loop(main))
    loop.run_forever()
    
