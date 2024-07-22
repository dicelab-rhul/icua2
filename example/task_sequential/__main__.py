"""Example that demonstrates tasks being sequentially enabled. TODO this is currently broken!"""

import pathlib
from icua.event import EnableTask
from icua.environment import MultiTaskEnvironment
from star_ray_pygame.avatar import Avatar
from star_ray.agent import Actuator, attempt
from star_ray_pygame.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
)
from star_ray_xml import Update
from task import MoveActuator

TASK_NAME = "task"
PATH = pathlib.Path(__file__).parent / TASK_NAME


class TaskActuator(Actuator):
    """Avatar actuator."""

    @attempt
    def default(
        self, action: MouseButtonEvent | MouseMotionEvent | KeyEvent | WindowCloseEvent
    ):
        """Forwards user input events."""
        return action

    @attempt
    def place(self, action: MouseButtonEvent) -> list[Update]:
        """Moves the circle element that is part of a clicked task to the mouse click position.

        Args:
            action (MouseButtonEvent): user action

        Returns:
            list[Update]: update actions
        """
        actions = []
        if action.button == MouseButtonEvent.BUTTON_LEFT:
            if action.status == MouseButtonEvent.DOWN:
                x, y = action.position
                for target in action.target:
                    if "task" in target:
                        actions.append(
                            Update.new(
                                f"//svg:svg[@id='{target}']/svg:circle",
                                dict(cx=x, cy=y),
                            )
                        )
        return actions

    @attempt
    def enable_task(self, action: KeyEvent) -> list[EnableTask]:
        """Enables a task based on a key press. There are three tasks: "1", "2" and "3" which can be enabled with the corresponding numerical key.

        Args:
            action (KeyEvent): user action.

        Returns:
            list[Enable]: action(s) to enable task(s).
        """
        if action.status and action.key in ["1", "2", "3"]:
            task_name = f"task-{action.key}"
            x = 110 * (int(action.key) - 1)
            context = dict(task_name=task_name, x=x, y=0, width=100, height=100)
            return [EnableTask(task_name=task_name, context=context)]
        return []


SVG = """<svg:svg id="root" xmlns:svg="http://www.w3.org/2000/svg" x="0" y="0" width="500" height="500"> </svg:svg>"""

avatar = Avatar([], [TaskActuator()])
env = MultiTaskEnvironment(avatar=avatar, enable_dynamic_loading=True, svg=SVG)
env.add_task(name=TASK_NAME, path=PATH, enable=False, agent_actuators=[MoveActuator])
env.rename_task(TASK_NAME, "task-1")

env.add_task(name=TASK_NAME, path=PATH, enable=False, agent_actuators=[MoveActuator])
env.rename_task(TASK_NAME, "task-2")

env.add_task(name=TASK_NAME, path=PATH, enable=False, agent_actuators=[MoveActuator])
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
