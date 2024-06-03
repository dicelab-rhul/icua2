import math
import random
from typing import Tuple
from pydantic import validator

from star_ray.event import Action
from star_ray_xml import XMLState, Template, Expr, update, select
from icua2.utils import LOGGER
from icua2.agent import Action, Actuator, attempt


class TrackingActuator(Actuator):

    @attempt
    def move_target(self, direction: Tuple[float, float] | int | float, speed: float):
        # an angle was provided (in degrees), convert it to a direction vector
        if isinstance(direction, (int, float)):
            angle = math.radians(direction)
            direction = (math.sin(angle), math.cos(angle))
        return TargetMoveAction(direction=direction, speed=speed)

    @attempt
    def perturb_target(self, speed: float):
        # print("perturb")
        angle = (random.random() * 2 - 1) * math.pi
        direction = (math.sin(angle), math.cos(angle))
        return TargetMoveAction(direction=direction, speed=speed)


# TODO ??
class TrackingModeAction(Action):

    manual: bool


class TargetMoveAction(Action):
    direction: Tuple[float, float]
    speed: float

    @validator("direction", pre=True, always=True)
    @classmethod
    def _validate_direction(cls, value):
        if isinstance(value, tuple):
            if len(value) == 2:
                # normalise the direction
                d = math.sqrt(value[0] ** 2 + value[1] ** 2)
                if d == 0:
                    return (0.0, 0.0)
                return (float(value[0]) / d, float(value[1]) / d)
        raise ValueError(f"Invalid direction {value}, must be Tuple[float,float].")

    @validator("speed", pre=True, always=True)
    @classmethod
    def _validate_speed(cls, value):
        return float(value)

    def execute(self, state: XMLState):
        if self.direction == (0.0, 0.0):
            LOGGER.warning(
                "Attempted %s with direction (0,0)", TargetMoveAction.__name__
            )
            return
        dx = self.direction[0] * self.speed
        dy = self.direction[1] * self.speed
        # get properties of the tracking task
        properties = state.select(
            select(
                xpath="//svg:svg/svg:svg[@id='task_tracking']",
                attrs=["width", "height"],
            )
        )[0]
        # task bounds should limit the new position
        x1, y1 = (0.0, 0.0)
        x2, y2 = x1 + properties["width"], y1 + properties["height"]

        new_x = Template(
            "max(min({x} + {dx}, {x2} - {width}), {x1})", dx=dx, x1=x1, x2=x2
        )
        new_y = Template(
            "max(min({y} + {dy}, {y2} - {height}), {y1})", dy=dy, y1=x1, y2=y2
        )
        return state.update(
            update(
                xpath="//svg:svg/svg:svg/svg:svg[@id='tracking_target']",
                attrs=dict(x=new_x, y=new_y),
            )
        )
