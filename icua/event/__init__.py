from typing import Tuple, Type

from star_ray_pygame.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
)

from star_ray_xml import XMLQuery, XPathQuery, Select, Update, Replace, Insert, Delete

from .event_task import EnableTask, DisableTask

from .event_guidance import (
    ShowGuidance,
    HideGuidance,
    XPathAction,
    DrawArrowAction,
    DrawBoxAction,
    DrawBoxOnElementAction,
    ShowElementAction,
    HideElementAction,
)

from .event_avatar import RenderEvent

# TODO try-except this?
from ..extras.eyetracking import EyeMotionEvent

USER_INPUT_TYPES: Tuple[Type] = (
    EyeMotionEvent,
    MouseMotionEvent,
    MouseButtonEvent,
    KeyEvent,
    WindowOpenEvent,
    WindowCloseEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
)

UserInputEvent = (
    MouseMotionEvent
    | MouseButtonEvent
    | KeyEvent
    | WindowOpenEvent
    | WindowCloseEvent
    | WindowFocusEvent
    | WindowMoveEvent
    | WindowResizeEvent
    | EyeMotionEvent
)


__all__ = (
    # user input events
    "UserInputEvent",
    "MouseEvent",
    "WindowEvent",
    "EyeMotionEvent",
    "MouseButtonEvent",
    "MouseMotionEvent",
    "KeyEvent",
    "WindowCloseEvent",
    "WindowFocusEvent",
    "WindowMoveEvent",
    "WindowOpenEvent",
    "WindowResizeEvent",
    # xml/svg events
    "XMLQuery",
    "XPathQuery",
    "Update",
    "Select",
    "Insert",
    "Delete",
    "Replace",
    # task events
    "EnableTask",
    "DisableTask",
    # guidance events
    "ShowGuidance",
    "HideGuidance",
    "XPathAction",
    "DrawArrowAction",
    "DrawBoxAction",
    "DrawBoxOnElementAction",
    "ShowElementAction",
    "HideElementAction",
)
