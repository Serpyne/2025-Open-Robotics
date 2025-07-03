import json
from os.path import join, dirname

class Status:
    Failure = 0xee
    Running = 0xff
    Success = 0xaa
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
        self.current_child: int = 0

    def tick(self, blackboard):
        print("select")
        while self.current_child < len(self.children):
            status = self.children[self.current_child].tick(blackboard)
            if status == Status.Running:
                return Status.Running
            elif status == Status.Success:
                self.current_child = 0
                return Status.Success
            self.current_child += 1
        self.current_child = 0
        return Status.Failure
class Sequence(Node):
    def __init__(self, children):
        self.children = children
        self.current_child: int = 0

    def tick(self, blackboard):
        while self.current_child < len(self.children):
            status = self.children[self.current_child].tick(blackboard)
            if status == Status.Running:
                return Status.Running
            elif status == Status.Failure:
                self.current_child = 0
                return Status.Failure
            self.current_child += 1
        self.current_child = 0
        return Status.Success
class Retry(Node):
    def __init__(self, child):
        self.child = child

    def tick(self, blackboard):
        status = self.child.tick(blackboard)
        if status == Status.Success:
            return Status.Success
        return Status.Running
class Action(Node):
    def __init__(self, func):
        self.func = func

    def tick(self, blackboard):
        if self.func(blackboard):
            return Status.Success
        return Status.Failure

class BehaviourTree:
    def __init__(self, tree_dict: dict, _globals: dict):
        self._tree_json: dict = tree_dict
        self._globals: dict = _globals
        self._behavior_tree: Node = self._build_tree(self._tree_json)

        self.blackboard: dict = {}

    def _build_tree(self, node_json) -> Node:
        node_type = node_json['type']
    
        if node_type == 'root':
            child = self._build_tree(node_json['child'])
            return Root(child)
    
        elif node_type == 'selector':
            children = [self._build_tree(child) for child in node_json['children']]
            return Selector(children)
    
        elif node_type == 'sequence':
            children = [self._build_tree(child) for child in node_json['children']]
            return Sequence(children)
    
        elif node_type == 'retry':
            child = self._build_tree(node_json['child'])
            return Retry(child)
    
        elif node_type == 'action':
            call_name = node_json['call']
            func = self._globals.get(call_name)
            if func is None:
                raise ValueError(f"Unknown action call: {call_name}")
            return Action(func)
    
        else:
            raise ValueError(f"Unknown node type: {node_type}")

    def tick(self) -> bool:
        return self._behavior_tree.tick(self.blackboard)
    
