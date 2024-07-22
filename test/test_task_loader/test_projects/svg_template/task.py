"""Test task."""

from star_ray.agent import Actuator, attempt
from star_ray.event import Action
from icua.utils._task_loader import avatar_actuator, agent_actuator


@avatar_actuator
class AvatarActuator(Actuator):  # noqa
    pass


@agent_actuator
class TaskActuator(Actuator):  # noqa
    @attempt
    def test(self):  # noqa
        pass


class MyAction(Action):  # noqa
    pass
