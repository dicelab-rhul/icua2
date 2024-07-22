"""Defines a `Sensor` that will subscribe to all user input events by default: `EyeMotionEvent`, `MouseMotionEvent`, `MouseButtonEvent`, `KeyEvent`, `WindowOpenEvent`, `WindowCloseEvent`, `WindowFocusEvent`, `WindowMoveEvent`, `WindowResizeEvent`."""

from typing import Any
from star_ray import Event, Sensor
from star_ray.pubsub import Subscribe

from ..event import USER_INPUT_TYPES


class UserInputSensor(Sensor):
    """Sensor that will subscribe to user input events."""

    def __init__(
        self,
        subscribe_to: tuple[type[Event]] = None,
        *args: list[Any],
        **kwargs: dict[str, Any],
    ):
        """Constructor.

        This sensor will subscribe to the following events: `EyeMotionEvent`, `MouseMotionEvent`, `MouseButtonEvent`, `KeyEvent`, `WindowOpenEvent`, `WindowCloseEvent`, `WindowFocusEvent`, `WindowMoveEvent`, `WindowResizeEvent`.

        Additional events can be added via the `subscribe_to` argument.

        Args:
            subscribe_to (tuple[Type[Event]], optional): additional user input event types to subscribe to. Defaults to None.
            args (list[Any]): Additional optional arguments.
            kwargs (dict[str,Any]): Additional optionals keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self._subscribe_to = list(USER_INPUT_TYPES)
        self._subscribe_to.extend(subscribe_to if subscribe_to else [])
        # remove duplicates if there are any
        self._subscribe_to = list(set(self._subscribe_to))

    def __subscribe__(self):  # noqa
        return [Subscribe(topic=event_type) for event_type in self._subscribe_to]
