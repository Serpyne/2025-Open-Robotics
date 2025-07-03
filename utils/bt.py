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
    def __init__(self, child):
        self.child = child

    def tick(self, blackboard):
        while True:
            if self.child.tick(blackboard):
                return True
        return False
class Action(Node):
    def __init__(self, func):
        self.func = func

    def tick(self, blackboard):
        return self.func(blackboard)

class BehaviourTree:
    def __init__(self, tree_dict: dict, _globals: dict):
        self._tree_json: dict = tree_dict
        self._globals: dict = _globals
        self._behavior_tree: Node = self._build_tree(self._tree_json)

        self.blackboard: dict = {}

    def _build_tree(self, node_json) ->Node:
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
    
