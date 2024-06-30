from .task_event import EnableTask, DisableTask, TaskEnabledEvent, TaskDisabledEvent

from star_ray.event import Event
from star_ray_pygame.event import (
    MouseMotionEvent,
    MouseButtonEvent,
    KeyEvent,
    WindowOpenEvent,
    WindowCloseEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
)

# TODO try this?
from icua2.extras.eyetracking import EyeMotionEvent


__all__ = (
    "Event",
    "EyeMotionEvent",
    "MouseMotionEvent",
    "MouseButtonEvent",
    "KeyEvent",
    "WindowOpenEvent",
    "WindowCloseEvent",
    "WindowFocusEvent",
    "WindowMoveEvent",
    "WindowResizeEvent",
    "EnableTask",
    "DisableTask",
    "TaskEnabledEvent",
    "TaskDisabledEvent",
)
