# here we need to define actions and actuators for the given task

from star_ray.agent import Actuator, attempt
from star_ray.event import Action
from icua2.utils._task_loader import avatar_actuator, agent_actuator


@avatar_actuator
class AvatarActuator(Actuator):
    pass


@agent_actuator
class TaskActuator(Actuator):

    @attempt
    def test(self):
        pass


class MyAction(Action):
    pass
