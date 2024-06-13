from icua2.agent import agent_actuator, attempt, Actuator
from star_ray_xml import update, Expr


@agent_actuator
class MoveActuator(Actuator):

    @attempt
    def move(self, direction):
        x = Expr("{value} + {direction}", direction=direction[0])
        y = Expr("{value} + {direction}", direction=direction[1])
        return update(
            xpath="//svg:svg/svg:circle",
            attrs=dict(cx=x, cy=y),
        )
