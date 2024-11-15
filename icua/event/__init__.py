"""Package defines or includes many useful event classes including task, guidance, UI, user input and XML/SVG related events."""

from star_ray import Event

from star_ray_pygame.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
    ScreenSizeEvent,
)


from star_ray_xml import (
    XMLQuery,
    XMLUpdateQuery,
    XPathQuery,
    Select,
    Update,
    Replace,
    Insert,
    Delete,
)

from .event_task import EnableTask, DisableTask

from .event_guidance import (
    TaskAcceptable,
    TaskUnacceptable,
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
from ..extras.eyetracking import EyeMotionEvent, EyeMotionEventRaw

USER_INPUT_TYPES: tuple[type] = (
    EyeMotionEvent,
    EyeMotionEventRaw,
    MouseMotionEvent,
    MouseButtonEvent,
    KeyEvent,
    WindowOpenEvent,
    WindowCloseEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
    ScreenSizeEvent,
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
    | ScreenSizeEvent
    | EyeMotionEvent
    | EyeMotionEventRaw
)


__all__ = (
    # user input events
    "UserInputEvent",
    "MouseEvent",
    "WindowEvent",
    "EyeMotionEvent",
    "EyeMotionEventRaw",
    "MouseButtonEvent",
    "MouseMotionEvent",
    "KeyEvent",
    "WindowCloseEvent",
    "WindowFocusEvent",
    "WindowMoveEvent",
    "WindowOpenEvent",
    "WindowResizeEvent",
    "ScreenSizeEvent",
    # xml/svg events
    "XMLQuery",
    "XMLUpdateQuery",
    "XPathQuery",
    "Update",
    "Select",
    "Insert",
    "Delete",
    "Replace",
    # task events
    "EnableTask",
    "DisableTask",
    "TaskAcceptable",
    "TaskUnacceptable",
    # guidance events
    "ShowGuidance",
    "HideGuidance",
    "XPathAction",
    "DrawArrowAction",
    "DrawBoxAction",
    "DrawBoxOnElementAction",
    "ShowElementAction",
    "HideElementAction",
    # misc
    "RenderEvent",
    "Event",
)
