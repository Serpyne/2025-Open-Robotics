"""

Main TS robot code; I plan to use this file in competitions.

"""

import sys
import os

file_path = os.path.dirname(__file__)
parent_dir = "\\".join(file_path.split("\\")[:-1])
sys.path.append(parent_dir)

from main import mainloop
from gpiozero import Button
from vector import Vector
import math
import asyncio
import json



def clamp(x, a: float = -1, b: float = 1) -> float:
    return min(max(x, a), b)
def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * clamp(t, 0, 1)
def normalise(a: float) -> float:
    return (a + 180) % 360 - 180

class Goal:
    Yellow = 0xea
    Blue = 0x89
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
    initial_heading: float = None
    last_seen_ball: int = 0
    has_ball: int = 0
    tof_distances: list[float] = []
    
    blind_milliseconds: int = 500
    target_goal: int = Goal.Yellow
    top_speed: float = 0.8
    dribble_speed: float = 0.5
    maintain_orientation_speed: float = 1 / 67
class Utilities:
    def __init__(self, motors=None, camera=None, compass=None, tofs=None):
        self.motors = motors
        self.camera = camera
        self.compass = compass
        self.tofs = tofs
        self.switch_left: Button = None
        self.switch_right: Button = None
class Robot:
    def __init__(self, motors, camera, compass, tofs):
        
        self.mode: int = Mode.Idle
        
        self.future_motor_speeds: list[float] = [0, 0, 0, 0]
        
        self.state: RobotState = RobotState()
        with open(os.path.join(file_path, "config.json"), "r") as f:
            self.config = json.load(f)
            f.close()
            
        self.state.blind_milliseconds = self.config["blindnessTimer"]
        self.state.top_speed = self.config["topSpeed"]
        self.state.target_goal = Goal.Blue if self.config["targetGoal"] == "blue" else Goal.Yellow
        self.state.maintain_orientation_speed = self.config["maintainOrientationTurnSpeed"]
        self.state.dribble_speed = self.config["dribbleSpeed"]
        
        self.speedBias = self.config["speedBias"]
        self.angleCoeff = self.config["anglePolyCoefficients"]
            
        self.utils: Utilities = Utilities(motors, camera, compass, tofs)
        self.utils.switch_left = Button(self.config["addresses"]["switchLeft"], pull_up=True)
        self.utils.switch_right = Button(self.config["addresses"]["switchRight"], pull_up=True)
        
        self.utils.camera.set_masks(self.config["cameraMasks"])
        self.update_interval: float = 1 / 60
        
    def calculate_final_direction(self, angle: float, distance: float) -> float:
        """DISTANCE IS IN CM"""
        
        def angle_poly(x: float) -> float:
            return (self.angleCoeff["x5"] * pow(x, 5)) + (self.angleCoeff["x4"] * pow(x, 4)) + (self.angleCoeff["x3"] * pow(x, 3)) + (self.angleCoeff["x2"] * pow(x, 2)) + (self.angleCoeff["x1"] * x)

        def f(x, a = 2.5, D = 21.0) -> float:
            return 1 / (1 + math.exp(-4 + (1 / a) * (x - D)))
            
        angle = normalise(angle)
        is_negative: bool = angle < 0
        
        mapped_angle: float = angle_poly(angle) if angle > 0 else -angle_poly(abs(angle))

        final_angle = angle + normalise(mapped_angle - angle) * f(distance)
        return normalise(final_angle)

    async def drive_in_direction(self, angle: float, speed: float, contribution: float = 1.0):
        FL = math.sin(math.radians(35 - angle))
        FR = math.sin(math.radians(35 + angle))

        if abs(FL) >= abs(FR):
            FR = (speed / abs(FL)) * FR
            FL = (speed / FL) * abs(FL)
        elif abs(FL) < abs(FR):
            FL = (speed / abs(FR)) * FL
            FR = (speed / FR) * abs(FR)
            
        self.future_motor_speeds[0] += FL * contribution
        self.future_motor_speeds[1] += FR * contribution
        self.future_motor_speeds[2] += -FL * contribution
        self.future_motor_speeds[3] += -FR * contribution
    async def turn(self, speed: float, contribution: float = 1.0):
        for i in range(4):
            self.future_motor_speeds[i] += clamp(speed * contribution, -1, 1)
    async def brake(self):
        self.utils.motors[0].set_speed(0)
        self.utils.motors[1].set_speed(0)
        self.utils.motors[2].set_speed(0)
        self.utils.motors[3].set_speed(0)
    
    async def confirm_drive(self):
        self.utils.motors[0].set_speed(self.future_motor_speeds[0])
        self.utils.motors[1].set_speed(self.future_motor_speeds[1])
        self.utils.motors[2].set_speed(self.future_motor_speeds[2])
        self.utils.motors[3].set_speed(self.future_motor_speeds[3])
        self.future_motor_speeds = [0, 0, 0, 0]
        
    async def enable_dribbler(self):
        self.utils.motors['dribbler'].set_speed(-1)
    async def stop_dribbler(self):
        self.utils.motors['dribbler'].set_speed(0)
    
    def determine_position(self) -> Vector:
        ...
        return
    
    def drive_direction_bias(self, a: float) -> float:
        # Drives more forward when its forward
        a = normalise(a)
        return a - a / ((1 / self.config["directionBias"]) * pow(a, 4) + 1)
        
    def drive_speed_bias(self, a: float) -> float:
        # Drives at 100% sideways and drives 100% on the sides.
        f = 1 - 0.5 * self.speedBias["sideDamping"] * (1 - math.cos(math.radians(2 * a)))
        # Composite function to make it so that the forward peak is
        # less than the backwards peaks, and the sides are independent
        g = 1 - self.speedBias["forwardDamping"] / (1 + pow(0.0167 * f, 4))
        # Lerp between the target speed and 100% depending on distance
        return lerp(g, 1, 1 / (1 + math.exp(15 - 0.5*a)))
    
    async def update(self):
        "Logic for the robot gameplay"
        
        update_duration = self.update_interval * 1000
        
        if None in [self.utils.camera.angle, self.utils.camera.distance]:
            
            await asyncio.sleep(0.1)
            
            if self.state.last_seen_ball <= 0:
                # await self.brake()
                await self.turn(0.1)
                await self.confirm_drive()
                # --
                # DRIVE TO MIDDLE OF FIELD
                return
            self.state.last_seen_ball -= 100 + update_duration
            self.state.last_seen_ball = max(0, self.state.last_seen_ball) # Milliseconds
            
        else:
            self.state.last_seen_ball = self.state.blind_milliseconds
            
            self.state.ball_angle = (180 - math.degrees(self.utils.camera.angle)) % 360
            self.state.ball_distance = self.utils.camera.distance
            
            
            
        if self.state.initial_heading is None:
            self.state.initial_heading = self.utils.compass.read()
        self.state.heading = normalise(self.utils.compass.read() - self.state.initial_heading)
        
        # self.state.position = self.determine_position() 
        # self.state.velocity
        # self.state.tof_distances = self.utils.tofs.read()
        
        
        
        normalised_ball_angle = normalise(self.state.ball_angle)
        
        
        
        # CHANGE THIS FOR "HELD BALL" BEHAVIOUR
        #if self.state.tofs["front"] < 5 or (abs(normalised_ball_angle) < 50 and self.state.ball_distance < 21.0):
        if abs(normalised_ball_angle) < 50 and self.state.ball_distance < 21.0: # NEED TO CALIBRATE TS
            self.state.has_ball = min(800, self.state.has_ball + update_duration)
        else:
            self.state.has_ball = max(0, self.state.has_ball - update_duration)
        
        
        
        if self.state.has_ball >= 300: # MUST HAVE HAD BALL FOR A SUBSTANTIAL AMOUNT
            # HAS BALL BEHAVIOUR
            if self.state.target_goal == Goal.Yellow:
                target_angle = self.utils.camera.yellow_angle
            else:
                target_angle = self.utils.camera.blue_angle
                
            if target_angle is not None:
                await self.turn(target_angle * .001, contribution=0.67)
                
            await self.drive_in_direction(0, self.state.dribble_speed, contribution = 1.0)
            await self.confirm_drive()
            
        else:
            # FOLLOW BALL BEHAVIOUR
            await self.turn(-self.state.heading * self.state.maintain_orientation_speed, contribution=0.4)
        
            direction = self.calculate_final_direction(normalised_ball_angle, self.state.ball_distance)
            direction = self.drive_direction_bias(direction)
            speed = self.drive_speed_bias(direction) * self.state.top_speed
        
            await self.drive_in_direction(direction, speed, contribution = 1.0)
            await self.confirm_drive()
            
            
        
    async def idle(self):
        "Robot is not moving or sensing"
        await self.brake()
        await self.stop_dribbler()
        await asyncio.sleep(0.5 - self.update_interval)
        
    async def calibrate(self):
        "Set initial heading"
        await self.brake()
        await self.stop_dribbler()
        self.state.initial_heading = self.utils.compass.read()
        await asyncio.sleep(0.5 - self.update_interval)

    async def start(self):
        
        await self.brake()
        await self.stop_dribbler()
        self.utils.camera.start_event_loop()
        self.utils.camera.show_debug_screen()
        
        while True:
            
            # if self.state.switch_left.is_pressed:
            #     self.state = Mode.Calibrate
            #     await self.calibrate()
                
            # elif self.state.switch_right.is_pressed:
            #     self.state = Mode.Update
            #     await self.update()
                
            # else:
            #     self.state = Mode.Idle
            #     await self.idle()
                
            await self.update()
                
            await asyncio.sleep(self.update_interval)



async def main(motors, camera, compass):
    ts = Robot(motors, camera, compass, None)
    await ts.start()
    
if __name__ == "__main__":
    with open(os.path.join(file_path, "config.json"), "r") as f:
        config = json.load(f)
        f.close()
        
    mainloop(main, motors=True, motor_addresses=config["addresses"]["motors"], dribbler_address=config["addresses"]["dribbler"],
            camera=True, screen=False, compass=True,
            tofs=False, tof_addresses=config["addresses"]["tofs"], capture_tof_address=config["addresses"]["captureTof"])
