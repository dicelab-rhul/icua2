import pathlib
from icua2 import MultiTaskEnvironment
from star_ray_pygame.avatar import Avatar
from star_ray.agent import Actuator, attempt
from star_ray.event.user_event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
)

TASK_NAME = "task_follow"
PATH = pathlib.Path(__file__).parent / "task"


class DefaultActuator(Actuator):

    @attempt(route_events=(MouseButtonEvent, MouseMotionEvent, KeyEvent))
    def default(self, action):
        return action


class ExitActuator(Actuator):

    @attempt(route_events=[WindowCloseEvent])
    def exit(self, action: WindowCloseEvent):
        assert isinstance(action, WindowCloseEvent)
        return action


avatar = Avatar(sensors=[], actuators=[ExitActuator(), DefaultActuator()])
env = MultiTaskEnvironment(agents=[avatar], enable_dynamic_loading=True)
env.register_task(name=TASK_NAME, path=PATH, enable=True)
env.run()
