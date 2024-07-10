from typing import Tuple, Type
from star_ray_pygame.event import *
# TODO try-except this?
from ..extras.eyetracking import EyeMotionEvent
from .task_event import EnableTask, DisableTask, TaskEnabledEvent, TaskDisabledEvent

USER_INPUT_TYPES: Tuple[Type] = (MouseMotionEvent,
                                 MouseButtonEvent,
                                 KeyEvent,
                                 WindowOpenEvent,
                                 WindowCloseEvent,
                                 WindowFocusEvent,
                                 WindowMoveEvent,
                                 WindowResizeEvent,
                                 EyeMotionEvent
                                 )

UserInputEvent = UserInputEvent | EyeMotionEvent

__all__ = (
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
    "XMLQuery",
    "XPathQuery",
    "Update",
    "Select",
    "Insert",
    "Delete",
    "Replace",
    "EnableTask",
    "DisableTask",
    "TaskEnabledEvent",
    "TaskDisabledEvent",
)
