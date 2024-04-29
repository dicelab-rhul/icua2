import pathlib
from icua2 import MultiTaskEnvironment

TASK_NAME = "task_follow"
PATH = pathlib.Path(__file__).parent / "task"

env = MultiTaskEnvironment(enable_dynamic_loading=True)
env.register_task(name=TASK_NAME, path=PATH, enable=True)
