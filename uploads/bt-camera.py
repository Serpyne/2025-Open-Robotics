import os
import sys
import math
import json
import asyncio

parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)

from utils.bt import BehaviourTree
from main import mainloop

angle = distance = None
orientation = -135
position = [0, 0]
oppGoalDirection = 0

def priority(bb):
    if checkIfBallIsNotVisible(bb):
        driveToGoal(bb)
        return True
    return False
        
def normaliseAngle(x: float):
    return (x + 180) % 360 - 180

def checkIfBallIsNotVisible(bb):
    if None in [angle, distance]:
        print("Ball covered")
        return True
    print("Ball visible")
    return False
def checkIfBallIsVisible(bb):
    if None in [angle, distance]:
        print("Ball visible")
        return False
    print("Ball covered")
    return True
def driveToGoal(bb):
    print("Driving to goal")
    bb.clear()
    return True
def conditionBallBehind(bb):
    if angle <= -90 or angle >= 90:
        return True
    return False
def conditionBallFront(bb):
    return not conditionBallBehind(bb)
def predictBallPath(bb):
    print("Predicting ball path")
    return True
def driveToBall(bb):
    if priority(bb): return False
    print("driving to ball")
    return True
def collectBall(bb):
    if priority(bb): return False
    driveToBall(bb)
    if checkIfBallIsNotVisible(bb):
        return False
    if distance > 50:
        print("ball not collected")
        return False
    print("ball collected")
    return True
def determineSide(bb):
    print("Determining side")
    # CHANGE THIS TO BE WHICHEVER SIDE OF THE FIELD WE ON
    bb["side"] = "Left"
    return True
def saveTurnDirectionToBlackboard(bb):
    if "side" not in bb:
        # determineSide(bb)
        return False
    if bb["side"] == "Left": bb["turnDirection"] = -135
    else:                    bb["turnDirection"] = 135
    return True
def saveTargetPosToBlackboard(bb):
    if "side" not in bb:
        return False
    if bb["side"] == "Left": bb["targetPos"] = [-0.9, -0.9] # Might need to change for non-normalised coords
    else:                    bb["targetPos"] = [0.9, -0.9]
    return True
TURN_THRESHOLD = 5.0
def turnToFaceDirection(bb):
    if priority(bb): return False
    if "turnDirection" not in bb:
        return False
    if abs(normaliseAngle(orientation - bb["turnDirection"])) > TURN_THRESHOLD:
        print("Not facing target direction")
        return False
    print("facing target direction")
    return True
TARGET_THRESHOLD = 50 # radial distance in mm ; also need to change to be mm or normalised idk
def driveToTargetPos(bb):
    if priority(bb): return False
    if "targetPos" not in bb:
        return False
    x, y = bb["targetPos"]
    if pow(position[0] - x, 2) + pow(position[1] - y, 2) > pow(TARGET_THRESHOLD, 2):
        print("Not at target pos")
        return False
    print("at target pos")
    return True
def turnToFaceGoal(bb):
    if priority(bb): return False
    # CHANGE THIS PLSS
    if abs(normaliseAngle(oppGoalDirection)) > TURN_THRESHOLD:
        print("not facing goal")
        return False
    print("facing goal")
    return True
def shoot(bb):
    print("Shooting")
    return True
        
async def main(camera):
    global angle, distance, orientation, position
    
    with open(os.path.join(parent_dir, "utils/bt.json")) as f:
        tree_string = json.load(f)
        f.close()
    bt = BehaviourTree(tree_string, globals())
    
    camera.start_event_loop()
    camera.show_debug_screen()
    
    while True:
        angle = camera.angle
        if angle is not None: angle = 90 - math.degrees(angle)
        distance = camera.distance
        
        bt.tick()
        print(angle, distance, "\n")
        print(bt.blackboard)
        await asyncio.sleep(1)
        
if __name__ == "__main__":
    mainloop(main, motors=False, camera=True)