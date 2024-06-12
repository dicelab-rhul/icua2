from typing import ClassVar, Tuple, List
from pydantic import Field
from star_ray.event import Event


class EyeMotionEvent(Event):
    """
    A class representing an eye tracking motion event.

    Attributes:
        id ([int]): A unique identifier for the event.
        timestamp ([float]): The timestamp (in seconds since UNIX epoch) when the event instance is created.
        source ([int]): A unique identifier for the source of this event.
        position: The position of the eyes relative to the window in pixels (px).
        velocity: The velocity of the eyes relative to the window in pixels per second (px/s).
        position_screen: The position of the eyes relative to the physical monitor or screen (normalised range [0,1])
        fixated: ([bool]): Whether the eye is fixated or saccadic based on gaze velocity or acceleration.
        in_window ([bool]): Whether the eye is within the ui window.
        target ([str]): The UI element that the mouse is currently over. This value is UI implementation dependent and may be None, typically it will be a unique element ID.
    """

    position: Tuple[float, float] | Tuple[int, int]
    velocity: Tuple[float, float] | Tuple[int, int]
    position_screen: Tuple[float, float] | Tuple[int, int]
    fixated: bool
    in_window: bool
    target: List[str] | None = Field(default_factory=lambda: None)
