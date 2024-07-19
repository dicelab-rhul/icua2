"""Defines a simple sensor that will subscribe to all user input events by default: `EyeMotionEvent`, `MouseMotionEvent`, `MouseButtonEvent`, `KeyEvent`, `WindowOpenEvent`, `WindowCloseEvent`, `WindowFocusEvent`, `WindowMoveEvent`, `WindowResizeEvent`. 
"""

from typing import Tuple, Type
from star_ray import Event, Sensor
from star_ray.pubsub import Subscribe

from ..event import USER_INPUT_TYPES


class UserInputSensor(Sensor):

    def __init__(self, subscribe_to: Tuple[Type[Event]] = None, *args, **kwargs):
        """Constructor.

        Args:
            subscribe_to (Tuple[Type[Event]], optional): events to subscribe to. Defaults to None, which will subscribe to the following events: `EyeMotionEvent`, `MouseMotionEvent`, `MouseButtonEvent`, `KeyEvent`, `WindowOpenEvent`, `WindowCloseEvent`, `WindowFocusEvent`, `WindowMoveEvent`, `WindowResizeEvent`.
        """
        super().__init__(*args, **kwargs)
        self._subscribe_to = subscribe_to if subscribe_to else tuple(USER_INPUT_TYPES)

    def __subscribe__(self):
        return [Subscribe(topic=event_type) for event_type in self._subscribe_to]
