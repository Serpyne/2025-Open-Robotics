import os
import json
from utils.bt import BehaviourTree

if __name__ == "__main__":
    parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
    print(parent_dir)