from star_ray.agent import Actuator, attempt
from star_ray_pygame.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowOpenEvent,
    WindowResizeEvent,
)

from icua2.extras.eyetracking.event import EyeMotionEvent


class DefaultActuator(Actuator):
    """This actuator will forward all user generated events to the environment. Other agents may subscribe to receive these events, otherwise they will simply be logged."""

    @attempt(
        route_events=(
            MouseButtonEvent,
            MouseMotionEvent,
            KeyEvent,
            EyeMotionEvent,
            WindowFocusEvent,
            WindowMoveEvent,
            WindowResizeEvent,
            WindowCloseEvent,
            WindowOpenEvent,
        )
    )
    def default(self, action):
        return action
