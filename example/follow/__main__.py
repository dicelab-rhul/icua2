import pathlib
from icua2 import MultiTaskEnvironment
from star_ray_pygame.avatar import Avatar
from star_ray.agent import Actuator, attempt
from star_ray_pygame.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
)
from star_ray_xml import update

TASK_NAME = "task_follow"
PATH = pathlib.Path(__file__).parent / "task"


class DefaultActuator(Actuator):

    @attempt
    def default(self, action: MouseButtonEvent | MouseMotionEvent | KeyEvent | WindowCloseEvent):
        return action

    def place(self, action: MouseButtonEvent):
        if action.button == MouseButtonEvent.BUTTON_LEFT:
            if action.status == MouseButtonEvent.DOWN:
                x, y = action.position
                return [
                    update(
                        xpath="//svg:svg/svg:circle",
                        attrs=dict(cx=x, cy=y),
                    )
                ]
        return []


avatar = Avatar(sensors=[], actuators=[DefaultActuator()])
env = MultiTaskEnvironment(agents=[avatar], enable_dynamic_loading=True)
env.register_task(name=TASK_NAME, path=PATH, enable=True)
env.run()
