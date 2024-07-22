"""Defines agent actuator for use in `task_sequential` example."""

from icua.agent import attempt, Actuator
from star_ray_xml import Update, Expr


class MoveActuator(Actuator):
    """Move actuator, will move the `circle` elements in a given direction."""

    @attempt
    def move(self, direction: tuple[float, float]) -> Update:
        """Move a `circle` element in the given direction.

        Args:
            direction (tuple[float, float]): direction to move.`

        Returns:
            Update: Updates the position of the element.
        """
        x = Expr("{cx} + {direction}", direction=direction[0])
        y = Expr("{cy} + {direction}", direction=direction[1])
        return Update.new(
            "//svg:svg/svg:circle",
            dict(cx=x, cy=y),
        )
