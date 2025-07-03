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

def checkIfBallIsNotVisible(bb):
    if None in [angle, distance]:
        return True
    return False
def checkIfBallIsVisible(bb):
    return not checkIfBallIsNotVisible(bb)
def driveToGoal(bb):
    print("Driving to goal")
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
    return True
def collectBall(bb):
    driveToBall(bb)
    if distance > 5:
        return False
    return True
def determineSide(bb):
    print("Determining side")
    bb["side"] = ["Left", "Right"][int(angle > 0)]
    return True
def saveTurnDirectionToBlackboard(bb):
    print("Saving turn direction")
    return True
def saveTargetPosToBlackboard(bb):
    print("Saving target position")
    return True
def turnToFaceDirection(bb):
    print("Turning to face direction")
    return True
def driveToTargetPos(bb):
    print("Driving to target position")
    return True
def turnToFaceGoal(bb):
    print("Turning to face goal")
    return True
def shoot(bb):
    print("Shooting")
    return True
        
async def main(camera):
    global angle, distance
    
    with open(os.path.join(parent_dir, "utils/bt.json")) as f:
        tree_string = json.load(f)
        f.close()
    bt = BehaviourTree(tree_string, globals())
    
    camera.start_event_loop()
    
    while True:
        angle = camera.angle
        if angle is not None: angle = 90 - math.degrees(angle)
        distance = camera.distance
        
        bt.tick()
        print(angle, distance, "\n")
        await asyncio.sleep(0.5)
        
if __name__ == "__main__":
    mainloop(main, motors=False, camera=True)