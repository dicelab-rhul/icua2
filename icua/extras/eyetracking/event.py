"""Module contains eyetracking event classes: `EyeMotionEvent` and `EyeMotionEventRaw`, see class documentation for details."""

from pydantic import Field
from star_ray.event import Event

__all__ = ("EyeMotionEvent", "EyeMotionEventRaw")


class EyeMotionEventRaw(Event):
    """A class representing an eyetracking motion event.

    Attributes:
        position (tuple[float,float]): The position of the eyes relative to the physical monitor or screen (typically in normalised range [0,1]).
    """

    position: tuple[float, float] | tuple[int, int]


class EyeMotionEvent(Event):
    """A class representing an eye tracking motion event with additional UI window information.

    Attributes:
        position (tuple[float,float]): The position of the eyes relative to the UI in svg space.
        position_raw  (tuple[float,float]): The position of the eyes relative to the UI in window space (pixels).
        position_screen (tuple[float,float]): The position of the eyes relative to the physical monitor or screen (typically in normalised range [0,1]).
        in_window (bool): Whether the eyes are within the ui window.
        target (list[str]): The UI elements that the eyes are currently over. This value is UI implementation dependent and may be None, typically it will contain unique element ids.
        fixated: (bool): Whether the eye are fixated or saccading based on gaze velocity or acceleration.
    """

    position: tuple[float, float] | tuple[int, int]
    position_raw: tuple[float, float] | tuple[int, int]
    position_screen: tuple[float, float] | tuple[int, int] | None
    fixated: bool
    in_window: bool
    target: list[str] | None = Field(default_factory=lambda: None)
