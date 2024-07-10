import pathlib
from icua2 import MultiTaskEnvironment, EnableTask, DisableTask
from star_ray_pygame.avatar import Avatar
from star_ray.agent import Actuator, attempt
from star_ray_pygame.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
)
from star_ray_xml import update

TASK_NAME = "task"
PATH = pathlib.Path(__file__).parent / "task"


class DefaultActuator(Actuator):

    @attempt
    def default(self, action: MouseButtonEvent | MouseMotionEvent | KeyEvent | WindowCloseEvent):
        return action

    @attempt
    def place(self, action: MouseButtonEvent):
        actions = []
        if action.button == MouseButtonEvent.BUTTON_LEFT:
            if action.status == MouseButtonEvent.DOWN:
                x, y = action.position
                for target in action.target:
                    if "task" in target:
                        actions.append(
                            update(
                                xpath=f"//svg:svg[@id='{target}']/svg:circle",
                                attrs=dict(cx=x, cy=y),
                            )
                        )
        return actions

    @attempt
    def enable_task(self, event: KeyEvent):
        if event.status and event.key in ["1", "2", "3"]:
            task_name = f"task-{event.key}"
            x = 110 * (int(event.key) - 1)
            context = dict(task_name=task_name, x=x,
                           y=0, width=100, height=100)
            return [EnableTask(task_name=task_name, context=context)]
        return []


SVG = """<svg:svg id="root" xmlns:svg="http://www.w3.org/2000/svg" x="0" y="0" width="500" height="500"> </svg:svg>"""

avatar = Avatar([], [DefaultActuator()])
env = MultiTaskEnvironment(
    agents=[avatar], enable_dynamic_loading=True, svg=SVG)
env.register_task(name=TASK_NAME, path=PATH, enable=False)
env.rename_task(TASK_NAME, "task-1")

env.register_task(name=TASK_NAME, path=PATH, enable=False)
env.rename_task(TASK_NAME, "task-2")

env.register_task(name=TASK_NAME, path=PATH, enable=False)
env.rename_task(TASK_NAME, "task-3")

env.enable_task(
    "task-1", context=dict(task_name="task-1", x=0, y=0, width=100, height=100)
)
env.enable_task(
    "task-2", context=dict(task_name="task-2", x=110, y=0, width=100, height=100)
)
env.enable_task(
    "task-3", context=dict(task_name="task-3", x=220, y=0, width=100, height=100)
)

env.run()
