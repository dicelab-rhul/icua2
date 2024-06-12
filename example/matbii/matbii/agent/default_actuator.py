from star_ray.agent import Actuator, attempt
from star_ray.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
)
from star_ray.event.user_event import (
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
    WindowCloseEvent,
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
        )
    )
    def default(self, action):
        return action
