"""Functions for extracting user input events from an event log file."""

import pandas as pd
from icua.extras.eyetracking import EyeMotionEvent
from icua.event import Event, MouseMotionEvent, MouseButtonEvent, KeyEvent, RenderEvent
from . import EventLogParser


def get_keyboard_events(
    parser: EventLogParser, events: list[tuple[float, Event]]
) -> pd.DataFrame:
    """Get keyboard events from a list of events.

    Columns:
        - timestamp: float - the timestamp of the event. This is not the logging timestamp, but the approximate timestamp of when user actually provided the input.
        - frame: int - the frame number of the event, events with a frame number of 0 happen BEFORE the first frame is rendered to the user.
        - key: str - the key that was pressed.
        - status: int - 0 for RELEASE (UP), 1 for PRESS (DOWN)

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.

    Returns:
        pd.DataFrame: dataframe with columns: ["timestamp", "key", "status"]
    """
    COLUMNS = ["timestamp", "frame", "key", "status"]
    keboard_events = parser.filter_events(events, KeyEvent | RenderEvent)
    keyboard_df = parser.as_dataframe(
        keboard_events,
        include=["timestamp", "key", "status"],
        include_frame=True,
    )
    return keyboard_df[COLUMNS]


def get_eyetracking_events(
    parser: EventLogParser, events: list[tuple[float, Event]]
) -> pd.DataFrame:
    """Get eye motion events from a list of events. Note that these events have been processed by filters that smooths and computes fixation information.

    Columns:
    - timestamp: float - the timestamp of the event. This is not the logging timestamp, but the approximate timestamp of when user actually provided the input.
    - frame: int - the frame number of the event, events with a frame number of 0 happen BEFORE the first frame is rendered to the user.
    - x: float - the x position of the mouse when the event occurred.
    - y: float - the y position of the mouse when the event occurred.
    - fixated: bool - whether the eyes are fixated or saccading based on the IVT filter.
    - target: list[str] - the ids of the UI elements that the mouse is hovering over.

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.

    Returns:
        pd.DataFrame: dataframe with columns: (timestamp, x, y, fixated, target)
    """
    COLUMNS = ["timestamp", "frame", "x", "y", "fixated", "target"]
    eye_motion_events = parser.filter_events(events, EyeMotionEvent | RenderEvent)
    # convert the events from a list to a dataframe. NOTE: that `timestamp_log` is used as the column name for the logging timestamp
    eye_motion_df = parser.as_dataframe(
        eye_motion_events,
        include=["timestamp", "position", "fixated", "target"],
        include_frame=True,
    )
    eye_motion_df["x"] = eye_motion_df["position"].apply(lambda p: p[0])
    eye_motion_df["y"] = eye_motion_df["position"].apply(lambda p: p[1])
    eye_motion_df.drop(columns=["position"], inplace=True)
    return eye_motion_df[COLUMNS]


def get_mouse_motion_events(
    parser: EventLogParser, events: list[tuple[float, Event]]
) -> pd.DataFrame:
    """Get mouse motion events from a list of events.

    Columns:
    - timestamp: float - the timestamp of the event. This is not the logging timestamp, but the approximate timestamp of when user actually provided the input.
    - frame: int - the frame number of the event, events with a frame number of 0 happen BEFORE the first frame is rendered to the user.
    - x: float - the x position of the mouse when the event occurred.
    - y: float - the y position of the mouse when the event occurred.
    - target: list[str] - the ids of the UI elements that the mouse is hovering over.

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.

    Returns:
        pd.DataFrame: dataframe with columns: (timestamp, x, y, target)
    """
    COLUMNS = ["timestamp", "frame", "x", "y", "target"]
    mouse_motion_events = parser.filter_events(events, MouseMotionEvent | RenderEvent)
    # convert the events from a list to a dataframe. NOTE: that `timestamp_log` is used as the column name for the logging timestamp
    mouse_motion_df = parser.as_dataframe(
        mouse_motion_events,
        include=["timestamp", "position", "target"],
        include_frame=True,
    )
    mouse_motion_df["x"] = mouse_motion_df["position"].apply(lambda p: p[0])
    mouse_motion_df["y"] = mouse_motion_df["position"].apply(lambda p: p[1])
    mouse_motion_df.drop(columns=["position"], inplace=True)
    return mouse_motion_df[COLUMNS]


def get_mouse_button_events(
    parser: EventLogParser, events: list[tuple[float, Event]]
) -> pd.DataFrame:
    """Get mouse button events from a list of events.

    Columns:
        - timestamp: float - the timestamp of the event. This is not the logging timestamp, but the approximate timestamp of when user actually provided the input.
        - frame: int - the frame number of the event, events with a frame number of 0 happen BEFORE the first frame is rendered to the user.
        - x: float - the x position of the mouse when the event occurred.
        - y: float - the y position of the mouse when the event occurred.
        - button: int - 1 for LEFT, 2 for MIDDLE, 3 for RIGHT
        - status: int - 0 for RELEASE (UP), 1 for PRESS (DOWN)
        - target: list[str] - the ids of the UI elements that the mouse is interacting with.

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.

    Returns:
        pd.DataFrame: dataframe with columns: ["timestamp", "x", "y", "button", "status", "target"]
    """
    COLUMNS = ["timestamp", "frame", "x", "y", "button", "status", "target"]
    # print(MouseButtonEvent.__module__ + "." + MouseButtonEvent.__name__)
    # filter events of interest, you can use any event type here, but we are interested in mouse button events
    mouse_button_events = parser.filter_events(events, MouseButtonEvent | RenderEvent)
    mouse_button_df = parser.as_dataframe(
        mouse_button_events,
        include=["timestamp", "position", "button", "status", "target"],
        include_frame=True,
    )
    mouse_button_df["x"] = mouse_button_df["position"].apply(lambda p: p[0])
    mouse_button_df["y"] = mouse_button_df["position"].apply(lambda p: p[1])
    mouse_button_df.drop(columns=["position"], inplace=True)
    return mouse_button_df[COLUMNS]
