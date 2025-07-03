import json
from os.path import join, dirname

class Node:
    def tick(self, blackboard):
        raise NotImplementedError()
class Root(Node):
    def __init__(self, child):
        self.child = child

    def tick(self, blackboard):
        return self.child.tick(blackboard)
class Selector(Node):
    def __init__(self, children):
        self.children = children

    def tick(self, blackboard):
        for child in self.children:
            if child.tick(blackboard):
                return True
        return False
class Sequence(Node):
    def __init__(self, children):
        self.children = children

    def tick(self, blackboard):
        for child in self.children:
            if not child.tick(blackboard):
                return False
        return True
class Retry(Node):
    def __init__(self, child, max_retries=3):
        self.child = child
        self.max_retries = max_retries

    def tick(self, blackboard):
        for _ in range(self.max_retries):
            if self.child.tick(blackboard):
                return True
        return False
class Action(Node):
    def __init__(self, func):
        self.func = func

    def tick(self, blackboard):
        return self.func(blackboard)
def build_tree(node_json) ->Node:
    node_type = node_json['type']

    if node_type == 'root':
        child = build_tree(node_json['child'])
        return Root(child)

    elif node_type == 'selector':
        children = [build_tree(child) for child in node_json['children']]
        return Selector(children)

    elif node_type == 'sequence':
        children = [build_tree(child) for child in node_json['children']]
        return Sequence(children)

    elif node_type == 'retry':
        child = build_tree(node_json['child'])
        return Retry(child)

    elif node_type == 'action':
        call_name = node_json['call']
        func = globals().get(call_name)
        if func is None:
            raise ValueError(f"Unknown action call: {call_name}")
        return Action(func)

    else:
        raise ValueError(f"Unknown node type: {node_type}")

class BehaviourTree:
    def __init__(self, tree_string: str):
        self._tree_json: dict = json.load(tree_string)
        self._behavior_tree: Node = build_tree(self._tree_json)

        # Example blackboard (can be a dict or a custom class)
        self.blackboard: dict = {}

    def tick(self) -> bool:
        return self._behavior_tree.tick(self.blackboard)
    
if __name__ == "__main__":
    def checkIfBallIsNotVisible(bb):
        print("Checking if ball is not visible")
        return True
    def driveToGoal(bb):
        print("Driving to goal")
        return True
    def checkIfBallIsVisible(bb):
        print("Checking if ball is visible")
        return True
    def conditionBallBehind(bb):
        print("Checking if ball is behind")
        return True
    def predictBallPath(bb):
        print("Predicting ball path")
        return True
    def driveToBall(bb):
        print("Driving to ball")
        return True
    def conditionBallFront(bb):
        print("Checking if ball is in front")
        return True
    def collectBall(bb):
        print("Collecting ball")
        return True
    def determineSide(bb):
        print("Determining side")
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

    tree_string = open(join(dirname(__file__), "bt.json"), "r")
    bt = BehaviourTree(tree_string)
    print(bt.tick())