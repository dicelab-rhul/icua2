"""Module contains eyetracking event classes: `EyeMotionEvent`, see class documentation for details."""

from pydantic import Field
from star_ray.event import Event


class EyeMotionEvent(Event):
    """A class representing an eye tracking motion event.

    Attributes:
        id (int): A unique identifier for the event.
        timestamp (float): The timestamp (in seconds since UNIX epoch) when the event instance is created.
        source (int): A unique identifier for the source of this event.
        position (tuple[float,float]): The position of the eyes relative to the UI window in pixels (px).
        position_screen (tuple[float,float]): The position of the eyes relative to the physical monitor or screen (typically in normalised range [0,1]).
        fixated: (bool): Whether the eye are fixated or saccading based on gaze velocity or acceleration.
        in_window (bool): Whether the eyes are within the ui window.
        target (list[str]): The UI elements that the eyes are currently over. This value is UI implementation dependent and may be None, typically it will contain unique element ids.
    """

    position: tuple[float, float] | tuple[int, int]
    position_screen: tuple[float, float] | tuple[int, int] | None
    fixated: bool
    in_window: bool
    target: list[str] | None = Field(default_factory=lambda: None)
